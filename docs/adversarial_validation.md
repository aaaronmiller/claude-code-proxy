# Adversarial Validation Report

## Objective
Identify flaws, logical gaps, and user experience issues in the Auto-Healing Wizard and Seamless Key Rotation system.

## Scenarios & Analysis

### 1. The "Doom Loop"
**Scenario**: User enters an invalid key in the wizard. The proxy reloads it, tries the request, gets 401 again. The wrapper sees 401, launches the wizard again.
**Risk**: High. The user is trapped in a loop if they keep pasting the wrong key.
**Mitigation**: The wrapper should detect if it has already run the wizard recently (maybe via a temp file flag) or allow the user to "Give Up" in the wizard, returning a specific exit code that stops the wrapper.

### 2. Profile Bloat (`.zshrc` Explosion)
**Scenario**: User runs the wizard 10 times.
**Current Behavior**: The wizard *appends* the export lines 10 times to `.zshrc`.
**Risk**: Medium. Makes the profile messy and potentially slow.
**Mitigation**: Use `sed` to replace existing lines if they exist, or use a dedicated `~/.claude_proxy_config` file sourced by `.zshrc`.

### 3. The "Slow Typist" Timeout
**Scenario**: User triggers 401. Proxy waits. User takes 2 minutes to find their key and paste it.
**Current Behavior**: Proxy times out after 60s (30 retries * 2s). Request fails.
**Risk**: Medium. Frustrating user experience.
**Mitigation**: Increase timeout to 5 minutes (300s).

### 4. "Pass" Key Mismatch
**Scenario**: User forgets to set `PROXY_AUTH_KEY=pass` in the alias or env.
**Current Behavior**: Proxy expects a real key. Client sends "pass". Proxy rejects it (401). Wrapper launches wizard. User enters real key. Wrapper restarts client with "pass". Proxy still rejects "pass".
**Risk**: High. The wizard fixes the *upstream* key, but the *downstream* auth is broken.
**Mitigation**: The wizard or wrapper should verify that `PROXY_AUTH_KEY` is set correctly in the environment or warn the user.

### 5. Shell Compatibility
**Scenario**: User uses `fish` shell.
**Current Behavior**: Wizard checks for `.zshrc`, `.bash_profile`, etc. Fails to find `fish` config.
**Risk**: Low (User specified zsh/bash context), but good to handle.
**Mitigation**: Add manual path entry (already exists) or explicit `fish` support.

### 6. Concurrent Access
**Scenario**: User has two terminal windows open.
**Current Behavior**: `source ~/.zshrc` in one doesn't affect the other.
**Risk**: Low. The wrapper explicitly tells the user to restart the proxy terminal or source the profile. The *Proxy* handles this via file polling, which is cross-process.

## Refinement Plan

1.  **Smart Profile Update**: Modify `api_key_wizard.sh` to replace existing lines instead of appending.
2.  **Extended Timeout**: Update `src/api/endpoints.py` to wait 300s.
3.  **Graceful Exit**: Update `run_router.sh` to check wizard exit code.
4.  **Startup Check**: Ensure `start_proxy.py` warns if `PROXY_AUTH_KEY` is missing when in proxy mode.
