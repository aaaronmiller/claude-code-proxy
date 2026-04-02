# Deliberative Review

This review applies the core idea behind the deliberative-refinement skill to the packaged folder: compress the state, inspect from multiple perspectives, and record concrete follow-up items instead of hand-wavy praise.

## Compressed State

- The project now has a single control plane in `bin/compressctl`.
- Installation flows are centralized in `scripts/quickstart.sh`.
- Runtime state is stored in `~/.config/input-compression/state.env`.
- Claude and Qwen receive RTK hook integration.
- Claude, Qwen, Codex, OpenCode, and OpenClaw receive launcher generation.

## Council Findings

### Operator

- The file-backed state switch is better than shell-global exports.
- `compressctl run <target>` provides a predictable non-interactive entry point for automation.

### Reliability

- The launcher strategy is safer than patching every CLI config blindly.
- Qwen compressed mode is intentionally explicit because it changes auth assumptions.

### Safety

- OpenClaw remains experimental instead of being silently rewritten into a proxy path it may not honor.
- The installer mutates only Claude and Qwen JSON settings, where the local format is understood.

### Packaging

- The project is now portable enough to copy to another machine and run.
- The old deploy script still works as a compatibility shim instead of breaking old notes.
- Arbitrary CLIs no longer block rollout because the generic wrapper path can route them without waiting for bespoke integration.

### Missing Pieces

- No automated smoke-test suite yet verifies each launcher on install.
- No uninstall script yet removes wrappers and restores hook state.
- No per-target health probe yet confirms the compressed launcher actually reaches the proxy.
- No config snapshot or rollback files are written before patching Claude and Qwen settings.

## Low-Effort Follow-Ups

1. Add `compressctl smoke <target>` for basic launch-path validation.
2. Add `compressctl uninstall` with backup-aware cleanup.
3. Write pre-patch backups for `~/.claude/settings.json` and `~/.qwen/settings.json`.
4. Record install metadata in `~/.config/input-compression/install.json`.
5. Add a small regression test harness that lints generated wrappers.

## Assessment

This folder is materially better than the previous live-state-only setup. It is not done. The next quality jump comes from smoke tests and rollback support, not from piling on more integrations blindly.
