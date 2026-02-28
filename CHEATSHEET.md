# Claude Code Proxy + CLIProxyAPIPlus Cheatsheet

## Architecture

```
Claude Code
  ├─ opus (BIG)    → proxy(:8082) → CLIProxyAPIPlus(:8317) → Antigravity/Kiro/Copilot
  ├─ sonnet (MID)  → proxy(:8082) → OpenRouter
  └─ haiku (SMALL) → proxy(:8082) → OpenRouter
```

---

## Starting Everything

### 1. CLIProxyAPIPlus (port 8317)

```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus \
  --config /home/cheta/code/cliproxyapi/config.yaml &
```

Verify: `curl -s http://127.0.0.1:8317/v1/models -H "Authorization: Bearer pass" | python3 -m json.tool`

### 2. Claude Code Proxy (port 8082)

```bash
cd ~/code/claude-code-proxy
source .venv/bin/activate
source .envrc
python start_proxy.py --skip-validation &
```

Verify: `curl -s http://127.0.0.1:8082/v1/messages -X POST -H "x-api-key: pass" -H "anthropic-version: 2023-06-01" -H "Content-Type: application/json" -d '{"model":"claude-opus-4-6-20250918","max_tokens":50,"messages":[{"role":"user","content":"ping"}]}'`

### 3. Claude Code (use the proxy)

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass claude
```

### One-liner startup (all three)

```bash
# Terminal 1: CLIProxyAPIPlus
/home/cheta/code/cliproxyapi/cli-proxy-api-plus --config /home/cheta/code/cliproxyapi/config.yaml

# Terminal 2: claude-code-proxy
cd ~/code/claude-code-proxy && source .venv/bin/activate && source .envrc && python start_proxy.py --skip-validation

# Terminal 3: Claude Code
ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass claude
```

---

## Adding Providers to CLIProxyAPIPlus

All login commands open a browser for OAuth. Credentials save to `~/.cli-proxy-api/`.
Auto-refresh runs every 15 minutes. Add `-incognito` for multi-account login.

**Antigravity** (Google-hosted Claude/Gemini — 10x limits)
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -antigravity-login --config /home/cheta/code/cliproxyapi/config.yaml
```

**Kiro** (AWS CodeWhisperer — Google OAuth)
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -kiro-login --config /home/cheta/code/cliproxyapi/config.yaml
```

**Kiro** (AWS Builder ID — better UX)
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -kiro-aws-authcode --config /home/cheta/code/cliproxyapi/config.yaml
```

**Kiro** (import from Kiro IDE if already logged in)
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -kiro-import --config /home/cheta/code/cliproxyapi/config.yaml
```

**Claude** (Anthropic OAuth)
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -claude-login --config /home/cheta/code/cliproxyapi/config.yaml
```

**Google Gemini CLI**
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -login --config /home/cheta/code/cliproxyapi/config.yaml
```

**OpenAI Codex**
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -codex-login --config /home/cheta/code/cliproxyapi/config.yaml
```

**GitHub Copilot**
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -github-copilot-login --config /home/cheta/code/cliproxyapi/config.yaml
```

**Qwen**
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -qwen-login --config /home/cheta/code/cliproxyapi/config.yaml
```

**iFlow**
```bash
/home/cheta/code/cliproxyapi/cli-proxy-api-plus -iflow-login --config /home/cheta/code/cliproxyapi/config.yaml
```

After adding a provider, CLIProxyAPIPlus auto-detects the new credential file and reloads. No restart needed.

### Check what's loaded

```bash
curl -s http://127.0.0.1:8317/v1/models -H "Authorization: Bearer pass" \
  | python3 -c "import json,sys; [print(f'{m[\"id\"]:40s} ({m[\"owned_by\"]})') for m in json.load(sys.stdin)['data']]"
```

---

## Testing Models

### Test via CLIProxyAPIPlus directly (port 8317)

```bash
curl -s -X POST http://127.0.0.1:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pass" \
  -d '{"model":"MODEL_ID","max_tokens":200,"messages":[{"role":"user","content":"Say hello"}]}' \
  | python3 -m json.tool
```

### Test via claude-code-proxy (port 8082, Claude API format)

```bash
curl -s -X POST http://127.0.0.1:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: pass" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-opus-4-6-20250918","max_tokens":200,"messages":[{"role":"user","content":"Say hello"}]}' \
  | python3 -m json.tool
```

### Test streaming (what Claude Code actually uses)

```bash
curl -s -X POST http://127.0.0.1:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: pass" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-opus-4-6-20250918","max_tokens":200,"stream":true,"messages":[{"role":"user","content":"Say hello"}]}'
```

---

## Switching Models

Edit `~/code/claude-code-proxy/.env`:

```bash
# BIG_MODEL goes through CLIProxyAPIPlus (Antigravity/Kiro)
BIG_MODEL="gemini-3-pro"                    # Gemini 3 Pro (free, always available)
# BIG_MODEL="claude-opus-4-6-thinking"      # Claude Opus 4.6 (10x limits, has quota)
# BIG_MODEL="claude-sonnet-4-5-thinking"    # Claude Sonnet 4.5 thinking
# BIG_MODEL="gemini-2.5-flash"              # Gemini 2.5 Flash (fast, free)
# BIG_MODEL="gemini-3-flash"                # Gemini 3 Flash

# MIDDLE/SMALL go through OpenRouter
MIDDLE_MODEL="openrouter/pony-alpha"
SMALL_MODEL="openrouter/pony-alpha"
```

Restart the proxy after changing `.env`:
```bash
kill $(pgrep -f "start_proxy.py") 2>/dev/null
cd ~/code/claude-code-proxy && source .venv/bin/activate && source .envrc && python start_proxy.py --skip-validation &
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `vibeproxy_unavailable` | CLIProxyAPIPlus not running — start it on :8317 |
| `RESOURCE_EXHAUSTED` / 429 | Model quota hit — switch BIG_MODEL or wait for reset |
| Empty text in responses | Reasoning model used all tokens thinking — increase max_tokens |
| `No endpoints found` (404) | OpenRouter privacy settings blocking free models — use non-free |
| `passthrough mode` | PROVIDER_API_KEY not set — run `source .envrc` before starting |
| Proxy not picking up .env changes | Kill and restart the proxy process |

### Check what's running

```bash
ss -tlnp | grep -E '8082|8317'
```

### Kill everything

```bash
kill $(pgrep -f "start_proxy.py") $(pgrep -f "cli-proxy-api") 2>/dev/null
```

---

## Key Files

| File | Purpose |
|---|---|
| `~/code/claude-code-proxy/.env` | Proxy config (models, endpoints, auth) |
| `~/code/claude-code-proxy/.envrc` | Activates venv, sets PROVIDER_API_KEY |
| `~/code/cliproxyapi/config.yaml` | CLIProxyAPIPlus config |
| `~/.cli-proxy-api/` | OAuth credential files (auto-managed) |
| `~/.secrets` | OPENROUTER_API_KEY |
