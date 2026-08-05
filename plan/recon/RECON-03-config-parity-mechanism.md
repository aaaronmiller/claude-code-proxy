---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, recon, config-parity, manifest, s1-02, read-only]
---

# Recon 03: Config parity mechanism (S1-02 prep, read-only)

Read-only inspection of `/home/cheta/code/claude-code-proxy`. Confirms how to add settings so
they reach all 4 surfaces automatically.

## The parity engine - `src/core/config_manifest.py`
- `Setting` dataclass (`:38`) fields: `env_var, type, default, cli_flag, tui_widget
  (input|toggle|select|number|textarea), web_component (input|switch|select|number|textarea|
  slider), choices, description, group`.
- One `Setting(...)` entry auto-generates the env var, CLI flag, TUI widget, and web component.
  This IS the single-source parity mechanism.
- Helpers: `get_group`, `get_all_groups`, `get_by_env_var`, `get_by_cli_flag`,
  `current_env_dict()`, `as_config_response()` (web), `GROUP_LABELS` (`:389`, TUI/web section
  labels).
- `src/core/config.py` holds 85 `ConfigField` runtime accessors (`:31`), each carrying
  cli_flag/tui_widget/web_component. (The "63 settings" doc figure has grown to ~85.)

## S1-02 is mechanical
- Add a `Setting` entry to the manifest -> it appears on .env/CLI/TUI/web with no per-surface code.
- AT: `current_env_dict()` and `as_config_response()` include it; `get_by_cli_flag("--x")` resolves;
  it renders in `--configure-advanced`.

## Important nuance: flat vs structured config
- FLAT scalars/toggles -> `Setting` in the manifest. From `05-CONFIG-SCHEMA.md` this covers:
  `allocator.enabled`, `allocator.solve_cadence`, `quota.drain_threshold`,
  `quota.provider_cooldown_s`, `memory.enabled/inject_limit/char_limit/project`,
  `compression.*` toggles, `model_scan.enabled/policy/cache_ttl_s`.
- NESTED records (lists/objects) -> NOT manifest Settings. These go through the specs/001
  `ConfigResolver` + `proxy_chain.json` model and their dedicated editors:
  `session_profiles[]` + per-role `floor`/`value_sensitivity`, `quota.adapters{}`,
  `chain[]`, `assignments[]`, `identifier_mappings[]`.
- So `05-CONFIG-SCHEMA.md` splits across two homes: flat keys via manifest, structured records via
  the resolver/proxy_chain.json. Both are still edited from all 4 surfaces (resolver guarantees
  it), just through different editor widgets.

## Conclusion
Sprint-1 prep recon complete. The parity path, quota/rotation substrate (RECON-02), capability
registry (RECON-01), and snapshot bind path are all confirmed present. Adding the new settings is
mechanical; the only genuinely-new code is the F18 LP layer and the multi-meter generalization of
`quota_sources.py`. No files changed. Code edits gated on DECISIONS.md O2.
