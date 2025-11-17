# Repository Cleanup Checklist

## Files to Remove Before Push

### Development/Testing Files
- [ ] `test_openrouter_key.py` - Testing script
- [ ] `.env.test` - Test environment
- [ ] `.env.gemini` - Gemini-specific config
- [ ] `switch_provider.sh` - Provider switcher script
- [ ] `TROUBLESHOOTING.md` - Temporary troubleshooting doc
- [ ] `PUSH.sh` - Push helper (contains tokens)

### Kiro IDE Files
- [ ] `.kiro/` - Entire directory (personal settings and specs)
  - `.kiro/specs/` - Development specs
  - `.kiro/steering/` - Personal steering rules
  - `.kiro/settings/` - IDE settings

### Model Usage Tracking
- [ ] `.model_usage.json` - Personal usage tracking

### Generated Files
- [ ] `models/` directory contents (will be regenerated at boot)
  - `models/model_limits.json`
  - `models/model_limits.csv`

## Commands to Clean

```bash
# Remove test files
rm -f test_openrouter_key.py .env.test .env.gemini switch_provider.sh TROUBLESHOOTING.md PUSH.sh

# Remove Kiro IDE directory
rm -rf .kiro/

# Remove model usage tracking
rm -f .model_usage.json

# Remove generated model database (will regenerate)
rm -rf models/*.json models/*.csv

# Verify gitignore is working
git status --ignored

# Add and commit
git add .
git commit -m "Clean repository for public release"
```

## Verify Before Push

1. **Check .gitignore is working:**
   ```bash
   git status --ignored
   ```
   Should show ignored files are not tracked

2. **No sensitive data:**
   ```bash
   grep -r "sk-" . --exclude-dir=.git --exclude-dir=.venv
   ```
   Should only find examples in .env.example

3. **README is current:**
   - All features documented
   - Examples are accurate
   - Links work

4. **Clean git status:**
   ```bash
   git status
   ```
   Should show only intended files

## What SHOULD Be Committed

✅ Source code (`src/`)
✅ Scripts (`scripts/`)
✅ Examples (`examples/`)
✅ Documentation (`README.md`, `LICENSE`)
✅ Configuration templates (`.env.example`)
✅ Requirements (`requirements.txt`, `pyproject.toml`)
✅ Startup script (`start_proxy.py`)
✅ Git configuration (`.gitignore`)

## What Should NOT Be Committed

❌ Personal configurations (`.env`, `.env.*`)
❌ IDE settings (`.kiro/`, `.vscode/`, etc.)
❌ Generated databases (`models/*.json`)
❌ Usage tracking (`.model_usage.json`)
❌ Test scripts (`test_*.py`)
❌ Temporary docs (`TROUBLESHOOTING.md`)
❌ Push helpers (`PUSH.sh`, `*AUDIT*.md`)
❌ API keys or tokens (anywhere!)
