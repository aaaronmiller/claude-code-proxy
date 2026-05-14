# Claude Code Proxy — Handoff Document

**Date:** 2026-04-16
**Status:** Proxies have just been restarted. All current codebase changes are active.

This document contains instructions and the current state for the next AI agent to continue work. The user's credits ran out for the current session, so you are picking up where the previous session left off.

## 🟢 What Was Just Completed (Do not repeat these)

1. **Streaming Usage Tracking**: Fixed missing tracking for streaming requests. `on_complete` callback is fully wired in `endpoints.py` and `response_converter.py`.
2. **Session Grouping**: Replaced naive request-based sessions with stable conversation fingerprints for multi-turn tool use.
3. **Log Noise Removed**: Properly implemented `uvicorn.access` log filter to silence `/health` and `/api/stats` polling.
4. **Circuit Breaker Persistence Fixed**: Rewired `client.py` to use `CircuitBreakerRegistry.get_sync()` so proxy states correctly persist across restarts.
5. **Security Audit Fix (RBAC)**: Fixed a massive vulnerability in `src/api/users_rbac.py` where password verification was using a tautology (`hash_password(password) == hash_password(password)`) and always returning valid. It now correctly checks `user_service.authenticate(username, password)`.
6. **Security Audit Fix (Hardcoded Secret)**: Removed the hardcoded fallback password `admin123` inside `src/services/user_management.py` auto-provisioning. It now preferentially uses `PROXY_DEFAULT_ADMIN_PASSWORD` from the environment or generates a 16-byte cryptographically secure URL-safe token.
7. **Security Audit Fix (Credential Logging Leak)**: Reduced the slice length of API keys printed directly into DEBUG logs from `[:20]` down to `[:8]` in `src/core/client.py`. This prevents credential harvesting in case the log file (`claude-code-proxy.log`) is exposed.
8. **Security Audit Fix (Path Traversal)**: Added a `validate_safe_filename()` sanitizer across 6+ API endpoints in `src/api/web_ui.py` (Profiles, Crosstalk Sessions, and Crosstalk Presets endpoints). The API previously used unsanitized web input directly in Path abstraction concatenations, which opened the proxy up to severe LFI (Local File Inclusion) or arbitrary file deletion attacks.
9. **Model Rankings Cron**: Added a crontab entry to refresh `data/free_model_rankings.json` every 6 hours.
10. **Documentation**: `README.md` and `CHANGELOG.md` are up to date.

---

## 🟡 Immediate Next Steps (Priority)

The following tasks need to be completed next. Start here.

### 1. Test "Option C" Reasoning Heartbeat (High Priority)
A major bug ("infinite lag" during stream stalls) was fixed by adding a heartbeat when upstream models emit `reasoning_content` that the client didn't request.
- **Action**: Test this fix. Have the user send a request through a reasoning model (e.g., `qwen/qwen3-235b-a22b:free` or `minimax/minimax-m2.5:free`) via Claude Code.
- **Verification**: You should see heartbeat dots `.` in the terminal while the model thinks, and the full reasoning text should be teed to `~/.cache/claude-code-proxy/reasoning/`.

### 2. Verify Web UI Realtime Page Build (Completed)
- **Status**: Tested via `npm run build` in this session. The build succeeds successfully without icon import errors.


### 3. Verify TUI & Tmux Status Bars (Medium Priority)
- **Action**: Ask the user to visually confirm that the Tmux status bars (configured by `proxies up`) are displaying live updates correctly.
- **Action**: Have the user launch `proxies sl` to verify the Statusline TUI launches cleanly and saves to `~/.claude/statusline-config.json`.

---

## ⚪ Long-Term Tasks (Low Priority)

Only tackle these after the immediate priorities are verified and stable.

### 1. Web UI Overhaul & Feature Parity
- **Goal**: Bring the Web Dashboard to full feature parity with the CLI and TUI.
- **Needs**: Analytics dashboard integration, model selection, and verifying the 3 new themes (Midnight Aurora, Ember Console, Synthwave Minimal).

### 2. Unified YAML Configuration
- **Goal**: The user requested adopting YAML over JSON for configuration. Env vars should have precedence over the file.
- **Needs**: Refactor `.env`/`config.json` loading logic in `src/core/config.py` to support a unified YAML format while maintaining backwards compatibility or migrating existing configs smoothly.

### 3. Log Rotation for Reasoning
- **Goal**: Prevent the `~/.cache/claude-code-proxy/reasoning/` directory from growing indefinitely.
- **Needs**: Add a log rotation script or prune mechanism (e.g., delete files older than 7 days) and hook it into the startup script or cron.

---

## 🧠 Guidance for the Next Agent
- **DO NOT** edit the circuit breaker or callbacks; they have already been audited and fixed.
- **DO NOT** use `cat` or `grep` inside bash commands; use your built-in `view_file` and `grep_search` tools.
- Your immediate focus should be **Verification of existing fixes**, specifically the stream stall fix and the Web UI build. If errors arise during verification, fix them immediately.
