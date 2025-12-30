# Production-Ready Features Guide

Comprehensive guide for config validation, profile management, and testing.

---

## Table of Contents

- [Config Validation](#config-validation)
- [Profile Manager](#profile-manager)
- [Test Suite](#test-suite)

---

## Config Validation

Automatically validates configuration on startup to catch errors early.

### Automatic Validation

Every time you start the proxy, configuration is validated:

```bash
python start_proxy.py
```

Output:
```
🔍 Validating configuration...

ERRORS:
1. PROVIDER_API_KEY is not set
  → Run: python start_proxy.py --setup
  → Or add to .env: PROVIDER_API_KEY="your-key-here"

💡 Run 'python start_proxy.py --setup' to fix configuration issues
```

### Manual Validation

Check configuration without starting the server:

```bash
python start_proxy.py --validate-config
```

Or directly:

```bash
python -m src.core.validator
```

### Skip Validation

Bypass validation checks (not recommended for production):

```bash
python start_proxy.py --skip-validation
```

### What Gets Validated

#### ✅ Required Variables

- `PROVIDER_API_KEY` or `OPENAI_API_KEY`
- `PROVIDER_BASE_URL` or `OPENAI_BASE_URL`
- At least one model configured (`BIG_MODEL`, `MIDDLE_MODEL`, or `SMALL_MODEL`)

#### ⚠️ Warnings

- Deprecated variable names (`OPENAI_API_KEY` → `PROVIDER_API_KEY`)
- Missing model configurations
- Incorrect OpenRouter format (missing `provider/` prefix)
- Short API keys (< 20 characters)
- Anthropic API keys (this proxy is for non-Anthropic providers)
- URLs without `/v1` suffix
- Hybrid mode with missing API keys
- Reasoning tokens outside recommended range

#### ❌ Errors

- Missing required variables
- Invalid URL format (must start with http:// or https://)
- Hybrid mode enabled but endpoint not set
- Non-numeric reasoning token values
- Invalid API keys (tested with provider /models endpoint)

### Example: Valid Configuration

```bash
# .env
PROVIDER_API_KEY="sk-or-v1-1234567890abcdef"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5:free"
```

Validation output:
```
🔍 Validating configuration...

CONFIGURATION:
  • Main Provider: API key validated ✓
  • Port 8082 is available

✅ Configuration validated successfully
```

### Example: Invalid Configuration

```bash
# .env
PROVIDER_API_KEY="short"  # Too short!
PROVIDER_BASE_URL="api.openai.com"  # Missing https://
BIG_MODEL="claude-sonnet"  # Wrong for OpenRouter
```

Validation output:
```
🔍 Validating configuration...

WARNINGS:
1. PROVIDER_API_KEY is very short (5 chars)
  → Most API keys are 30+ characters
  → Make sure you copied the full key

2. BIG_MODEL="claude-sonnet" may be incorrect for OpenRouter
  → OpenRouter models use format: provider/model
  → Example: anthropic/claude-sonnet-4
  → Run: python -m src.cli.model_selector

ERRORS:
1. PROVIDER_BASE_URL must start with http:// or https://
  → Current value: api.openai.com

❌ Configuration validation failed

💡 Run 'python setup_wizard.py' to fix configuration issues
```

### Strict Mode

Treat warnings as errors:

```bash
python -m src.core.validator --strict
```

---

## Profile Manager

Easily switch between different configurations (dev, prod, testing, etc.).

### Quick Start

**Interactive mode:**
```bash
python -m src.cli.profile_manager
```

Shows menu:
```
====================================================================
💾 Profile Manager
====================================================================

What would you like to do?
❯ 📋 List profiles
  🔄 Switch to profile
  ➕ Create new profile
  ❌ Delete profile
  🔍 Compare profiles
  📤 Export profile
  📥 Import profile
  🚪 Exit
```

### List Profiles

**CLI:**
```bash
python -m src.cli.profile_manager list
```

**Output:**
```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Name        ┃ Provider          ┃ BIG Model             ┃ Modified        ┃ Description   ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ development │ localhost:11434   │ qwen2.5:72b           │ 2025-11-22 09:30│ Local dev     │
│ production  │ openrouter.ai     │ anthropic/claude-so.. │ 2025-11-21 14:22│ Production    │
│ testing     │ generativelang... │ gemini-3-pro-previe.. │ 2025-11-20 11:15│ Testing setup │
└─────────────┴───────────────────┴───────────────────────┴─────────────────┴───────────────┘
```

### Switch Profiles

**CLI:**
```bash
python -m src.cli.profile_manager switch production
```

**Output:**
```
📦 Backed up current .env to .env.backup.20251122_103045

✅ Switched to profile: production

Active Configuration:
  Provider: https://openrouter.ai/api/v1
  BIG Model: anthropic/claude-sonnet-4
  MIDDLE Model: google/gemini-pro-1.5
  SMALL Model: google/gemini-flash-1.5:free
```

**What happens:**
1. Current `.env` backed up to `.env.backup.TIMESTAMP`
2. Profile copied to `.env`
3. Configuration summary displayed

**Restart proxy to use new config:**
```bash
pkill -f start_proxy.py
python start_proxy.py
```

### Create Profile

**From current .env:**
```bash
python -m src.cli.profile_manager create my-setup "My custom configuration"
```

**What happens:**
1. Reads current `.env`
2. Adds description and timestamp
3. Saves to `profiles/my-setup.env`

**Profile file:**
```bash
# Description: My custom configuration
# Created: 2025-11-22 10:35:12
#
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
...
```

### Delete Profile

**CLI:**
```bash
python -m src.cli.profile_manager delete old-config
```

**Confirmation:**
```
Are you sure you want to delete profile 'old-config'? (y/N):
```

### Compare Profiles

**CLI:**
```bash
python -m src.cli.profile_manager compare development production
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Variable            ┃ development       ┃ production            ┃ Status     ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ PROVIDER_BASE_URL   │ localhost:11434/v1│ openrouter.ai/api/v1  │ ✗ Different│
│ BIG_MODEL           │ qwen2.5:72b       │ anthropic/claude-so..│ ✗ Different│
│ MIDDLE_MODEL        │ qwen2.5:14b       │ google/gemini-pro-1.5│ ✗ Different│
│ ENABLE_DASHBOARD    │ true              │ false                 │ ✗ Different│
│ HOST                │ 0.0.0.0           │ 0.0.0.0               │ ✓ Same     │
└─────────────────────┴───────────────────┴───────────────────────┴────────────┘
```

### Export Profile

**Share a profile:**
```bash
python -m src.cli.profile_manager export production ~/shared/prod-config.env
```

### Import Profile

**From shared file:**
```bash
python -m src.cli.profile_manager import ~/shared/prod-config.env production
```

**Auto-name from filename:**
```bash
python -m src.cli.profile_manager import custom-setup.env
# Saves as 'custom-setup' profile
```

### Common Workflows

#### Setup Development Environment

```bash
# 1. Configure for local development
python setup_wizard.py
# Select: Ollama, qwen2.5:72b, enable dashboard

# 2. Save as development profile
python -m src.cli.profile_manager create development "Local Ollama setup"

# 3. Configure for production
python setup_wizard.py
# Select: OpenRouter, real models, disable dashboard

# 4. Save as production profile
python -m src.cli.profile_manager create production "Production OpenRouter"
```

#### Switch Between Environments

```bash
# Development
python -m src.cli.profile_manager switch development
python start_proxy.py

# Production
python -m src.cli.profile_manager switch production
python start_proxy.py

# Testing (Gemini free)
python -m src.cli.profile_manager switch testing
python start_proxy.py
```

#### Share Configuration with Team

```bash
# Export your setup
python -m src.cli.profile_manager export my-setup team-config.env

# Team member imports
python -m src.cli.profile_manager import team-config.env shared-setup
python -m src.cli.profile_manager switch shared-setup
```

---

## Test Suite

Comprehensive pytest suite with 70+ tests for production quality.

### Quick Start

**Run all tests:**
```bash
python run_tests.py
```

**With coverage:**
```bash
python run_tests.py --cov
```

**Output:**
```
🧪 Running tests...

tests/test_config_loading.py::TestConfigLoading::test_load_provider_config PASSED [ 5%]
tests/test_config_loading.py::TestConfigLoading::test_load_model_config PASSED [10%]
tests/test_model_mapping.py::TestModelMapping::test_claude_opus_maps_to_big_model PASSED [15%]
...

=============================== 70 passed in 2.34s ================================

---------- coverage: platform linux, python 3.11.7 -----------
Name                               Stmts   Miss  Cover
------------------------------------------------------
src/core/config.py                   156     12    92%
src/core/model_manager.py             89      5    94%
src/core/validator.py                287     23    92%
src/cli/profile_manager.py           234     31    87%
------------------------------------------------------
TOTAL                                766     71    91%

Coverage HTML written to htmlcov/index.html
```

### Run Specific Tests

**Single file:**
```bash
pytest tests/test_model_mapping.py -v
```

**Single test:**
```bash
pytest tests/test_model_mapping.py::TestModelMapping::test_claude_opus_maps_to_big_model -v
```

**By keyword:**
```bash
pytest -k "validation" -v  # All validation tests
pytest -k "profile" -v     # All profile tests
```

### Test Categories

**Model Mapping (9 tests):**
- Claude model name → configured model
- OpenRouter format validation
- Case-insensitive matching
- Suffix notation for reasoning
- Pass-through for non-Claude models

**Config Loading (13 tests):**
- Environment variable parsing
- Legacy variable support
- Default values
- Boolean/integer parsing
- Hybrid mode configuration
- Terminal output settings
- Custom prompts

**Validator (21 tests):**
- Required variable checks
- Deprecated variable warnings
- Invalid reasoning config detection
- OpenRouter format validation
- Hybrid mode validation
- API key testing (401, 403)
- Common mistake detection
- Strict mode behavior

**Profile Manager (15 tests):**
- Create/list/switch/delete profiles
- Profile comparison
- Import/export functionality
- Metadata preservation
- Error handling

### Coverage Reports

**Terminal:**
```bash
python run_tests.py --cov
```

**HTML (detailed):**
```bash
python run_tests.py --cov
open htmlcov/index.html
```

Shows:
- Line-by-line coverage
- Missing branches
- Functions not tested
- Interactive drill-down

### Continuous Integration

**GitHub Actions:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install uv
      - run: uv sync
      - run: python run_tests.py --cov
```

### Writing New Tests

**Example:**
```python
# tests/test_my_feature.py
import pytest
from src.my_module import my_function

class TestMyFeature:
    """Test my new feature"""

    def test_basic_case(self, sample_config):
        """Test basic functionality"""
        result = my_function("input")
        assert result == "expected"

    def test_edge_case(self, clean_env):
        """Test edge case"""
        result = my_function(None)
        assert result is None
```

**Run new tests:**
```bash
pytest tests/test_my_feature.py -v
```

---

## Integration Examples

### Full Development Workflow

```bash
# 1. Setup
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# 2. Configure development environment
python setup_wizard.py
# → Choose Ollama, local models

# 3. Save as dev profile
python -m src.cli.profile_manager create development "Local dev setup"

# 4. Validate configuration
python start_proxy.py --validate-config

# 5. Run tests
python run_tests.py --cov

# 6. Start proxy
python start_proxy.py

# 7. Test with Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "test prompt"
```

### Production Deployment

```bash
# 1. Create production profile
python setup_wizard.py
# → Choose OpenRouter, production models

python -m src.cli.profile_manager create production "Production config"

# 2. Validate before deploying
python -m src.cli.profile_manager switch production
python start_proxy.py --validate-config

# 3. Run tests
python run_tests.py

# 4. Deploy
python start_proxy.py
```

### Testing Different Providers

```bash
# 1. Create profiles for each provider
python setup_wizard.py  # Gemini
python -m src.cli.profile_manager create gemini "Google Gemini free"

python setup_wizard.py  # OpenRouter
python -m src.cli.profile_manager create openrouter "OpenRouter"

python setup_wizard.py  # Local
python -m src.cli.profile_manager create local "Ollama local"

# 2. Test each
for profile in gemini openrouter local; do
    echo "Testing $profile..."
    python -m src.cli.profile_manager switch $profile
    python start_proxy.py --validate-config
done

# 3. Compare configurations
python -m src.cli.profile_manager compare gemini openrouter
python -m src.cli.profile_manager compare openrouter local
```

---

## Troubleshooting

### Validation Fails on Startup

**Problem:**
```
❌ Configuration validation failed
```

**Solution:**
```bash
# Check what's wrong
python start_proxy.py --validate-config

# Fix with wizard
python setup_wizard.py

# Or bypass (not recommended)
python start_proxy.py --skip-validation
```

### Profile Switch Not Working

**Problem:**
Profile switched but proxy still uses old config

**Solution:**
```bash
# Restart proxy after switching
pkill -f start_proxy.py
python start_proxy.py
```

### Tests Failing

**Problem:**
```
FAILED tests/test_model_mapping.py::test_claude_opus_maps_to_big_model
```

**Solution:**
```bash
# Run with verbose output
pytest tests/test_model_mapping.py -vv

# Check for environment conflicts
python -m src.core.validator

# Reinstall dependencies
uv sync
```

---

## Best Practices

### Configuration Management

1. **Always validate before deploying:**
   ```bash
   python start_proxy.py --validate-config
   ```

2. **Use profiles for different environments:**
   - `development` - Local testing
   - `staging` - Pre-production
   - `production` - Live deployment

3. **Version control profiles:**
   ```bash
   git add profiles/*.env
   git commit -m "Update production profile"
   ```

### Testing

1. **Run tests before committing:**
   ```bash
   python run_tests.py --cov
   ```

2. **Maintain coverage above 90%:**
   ```bash
   pytest --cov=src --cov-fail-under=90
   ```

3. **Write tests for new features:**
   - Unit tests for logic
   - Integration tests for API
   - Validation tests for config

### Profile Management

1. **Document profiles:**
   ```bash
   python -m src.cli.profile_manager create prod "Production: OpenRouter with Claude Sonnet"
   ```

2. **Back up before switching:**
   - Automatic backups to `.env.backup.TIMESTAMP`
   - Can restore if needed

3. **Share team configurations:**
   ```bash
   python -m src.cli.profile_manager export team-standard ~/shared/
   ```

---

## Summary

**Config Validation:**
- ✅ Automatic on startup
- ✅ Clear error messages
- ✅ API key testing
- ✅ Common mistake detection

**Profile Manager:**
- ✅ Easy environment switching
- ✅ Import/export for sharing
- ✅ Profile comparison
- ✅ Automatic backups

**Test Suite:**
- ✅ 70+ comprehensive tests
- ✅ 91% code coverage
- ✅ CI/CD ready
- ✅ Easy to extend

**Production Ready!** 🎉
