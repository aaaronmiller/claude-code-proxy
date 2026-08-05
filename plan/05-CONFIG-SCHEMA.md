---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, config, schema, gateway-yaml, proxy-chain, additive, parity]
---

# Unified Config Schema (additive extension of specs/001)

Do NOT invent a parallel config. specs/001 already ships the spine: structured config in
`config/proxy_chain.json` (schema_version "2.0.0") resolved by `ConfigResolver` (precedence CLI >
shell env > .env > stored > defaults), with `Assignment` / `IdentifierMapping` / `ProxyChain` /
`ProxyEntry` records, audit log, and migration. Secrets live in `.env` as `${VAR}` refs only.

This doc defines the ADDITIVE sections for the new core (F06 quota, F18 allocator, F09 memory,
F08 compression knobs, session roles/profiles). Bump schema_version 2.0.0 -> 2.1.0 with
auto-migration (specs/001 FR-023a). Every new key MUST be registered in
`src/core/config_manifest.py` so it inherits .env/CLI/TUI/WebUI parity automatically; secrets stay
in `.env`, never in the structured file.

Shown as annotated YAML for readability; persists as the JSON `proxy_chain.json` model (or a
`gateway.yaml` view over the same resolver). Existing sections summarized; new sections in full.

## Existing (specs/001, unchanged)

```yaml
schema_version: "2.1.0"
assignments:            # tier + slot bindings (unchanged Assignment record)
  - {id: big,    kind: tier, model: ..., provider: ..., base_url: ..., api_key: "${...}", enabled: true, cascade: [...]}
identifier_mappings: [...]   # incoming-identifier -> assignment
chain:                  # ProxyEntry[] ; the proxy is itself an entry; reorderable from all surfaces
  - {id: headroom, order: 0, enabled: true, url: "http://127.0.0.1:8787", ...}
  - {id: rtk,      order: 1, enabled: true, ...}
  - {id: cliproxyapi, order: 2, enabled: false, ...}
  - {id: gateway,  order: 3, enabled: true, ...}
router: {...}
```

## NEW: model_scan (align to specs/003; mostly exists)

```yaml
model_scan:
  enabled: true
  snapshot_path: "~/.config/model-scan/routing_snapshot.json"
  policy: "rotate"            # static|free|budget:<x>|quality|roles|rotate
  cache_ttl_s: 900
  staleness_limit_s: 86400
  free_floor_preferred: "deepseek/deepseek-v4-flash:free"
  lanes:
    standby:     {pool: free,           never_paid: true}
    interactive: {pool: paid_plus_free, policy: rotate}
```

## NEW: roles and session profiles (F18 inputs)

```yaml
session_profiles:           # "character sheets"; instantiated per running session
  pi-economy:
    start_mode: hybrid       # rollup | precomputed | hybrid
    roles:
      primary:  {floor: {min_tier: B, min_value: deepseek-v4-flash}, value_sensitivity: 0.1, fallback_depth: 4, diversity_cap: 0.6, importance: 0.4}
      toolcall: {floor: {needs_tools: true, min_value: gpt-oss-120b}, value_sensitivity: 0.1, fallback_depth: 4}
  pi-premium:
    start_mode: hybrid
    roles:
      primary:  {floor: {min_tier: A, needs_tools: true}, value_sensitivity: 0.9, fallback_depth: 5, importance: 0.8}
      toolcall: {floor: {needs_tools: true, min_value: gpt-oss-120b}, value_sensitivity: 0.4}
  hermes-full:
    start_mode: rollup
    roles:
      primary:    {floor: {min_tier: A, needs_tools: true}, value_sensitivity: 1.0, importance: 1.0}
      delegation: {floor: {min_tier: A}, value_sensitivity: 0.8, importance: 0.9}
      aux:        {floor: {min_value: gpt-oss-120b}, value_sensitivity: 0.05, count: 10}   # satisficing
      vision:     {floor: {needs_vision: true}, value_sensitivity: 0.5}
      compression:{floor: {min_ctx: 200000}, value_sensitivity: 0.3}
  cc-standard:
    roles:
      big:    {floor: {min_tier: A}, value_sensitivity: 0.9}
      middle: {floor: {min_tier: B}, value_sensitivity: 0.4}
      small:  {floor: {min_value: gpt-oss-120b}, value_sensitivity: 0.1}
```

floor + value_sensitivity per role are the user-defined satisfice/maximize knobs (see F18 section
1). Aux roles default to value_sensitivity ~0 so scarce smart capacity is preserved.

## NEW: quota (F06 meters + adapters)

```yaml
quota:
  enabled: true
  ledger_db: "${USAGE_TRACKING_DB_PATH}"     # reuse usage SQLite
  adapters:                                   # enable + access pattern per provider
    claude_code: {pattern: header}
    codex:       {pattern: header}
    cerebras:    {pattern: header}
    groq:        {pattern: header}
    openrouter:  {pattern: poll, endpoint: "/api/v1/auth/key"}
    ollama:      {pattern: scrape, every: weekly}
    antigravity: {pattern: scrape, rescan_proc_s: 30}
    opencode_go: {pattern: local_sqlite}
    nvidia_nim:  {pattern: estimate, rpm: 35}
    kiro:        {pattern: poll}
    perplexity:  {pattern: header}
  meters_source_of_truth: headers            # never JSONL token counts
  drain_threshold: 0.15
  provider_cooldown_s: 600
```

## NEW: allocator (F18)

```yaml
allocator:
  enabled: true
  solver: ortools                 # ortools|pulp|scipy
  solve_cadence: per_model_scan_cycle   # + on fleet/quota change
  horizon_seconds: 86400
  online:
    enforcement: token_bucket
    refiner: thompson_bandit      # explores within LP-chosen candidate set
  preemption:
    idle_threshold_s: 2700        # 45 min
    demotion_depth: 1             # drop idle session this many tiers
    hysteresis_s: 300
  importance_source: profile      # profile|launch_arg
  weekly_report: true             # bench-time / regret / shadow-prices
```

## NEW: memory (F09 wiki-memory)

```yaml
memory:
  enabled: true
  backend: wiki-memory
  ai_wiki: "${AI_WIKI}"
  memory_db: "${MEMORY_DB}"        # $AI_WIKI/.meta/memory.json
  project: "${MEMORY_PROJECT}"     # set explicitly; do not infer from cwd
  inject_limit: 6
  char_limit: 4000                 # cap injection tokens
  store_policy: explicit_plus_optin   # explicit "remember" always; else opt-in per session
  clawmem: {enabled: false, url: "http://localhost:7438"}   # optional warm tier
  write_lock: true                 # JSON store has no locking; required for concurrent writes
hooks:
  emulation: true                  # provide session-start/pre-request/post-response/session-end to non-hook CLIs
  output_form: auto                # auto|plain|claude_structured|hermes_context
```

## NEW: compression (F08 knobs; many already env)

```yaml
compression:
  headroom: {enabled: true, port: 8787, bypass_threshold: ..., tool_schema_strip: false}
  rtk:      {enabled: true, surface_stats: true}     # surface_stats fixes the missing RTK stats
  context_engine: {engine: none}   # none|hermes-lcm|pi-prune (never both)
```

## Secrets (.env only, never in structured file)

```
PROVIDERS_openrouter_API_KEY=...
PROVIDERS_openrouter_API_KEYS=k1,k2,k3      # key pool for rotate-on-429
AI_WIKI=~/.local/share/ai-wiki
MEMORY_PROJECT=gateway
# ANTHROPIC_API_KEY=pass / PROXY_AUTH_KEY=pass : SDK requirements, do not modify
```

## Parity + migration rules

- Two homes (see RECON-03): FLAT scalars/toggles (allocator.enabled, quota.drain_threshold,
  memory.inject_limit, compression toggles, model_scan.policy) register as `Setting` entries in
  `config_manifest.py` and auto-surface on all 4 surfaces. NESTED records (session_profiles[] with
  per-role floor/value_sensitivity, quota.adapters{}, chain[], assignments[]) live in the specs/001
  `ConfigResolver` + proxy_chain.json model with dedicated editor widgets. Both remain editable
  from all 4 surfaces via the resolver.
- CI grep forbids direct `os.environ.get` outside config modules (specs/001). TUI/WebUI edit via
  the same resolver; CLI args override temporarily.
- schema_version 2.0.0 -> 2.1.0 additive; auto-migrate with backup, halt on unsafe (specs/001
  FR-023a/c). Legacy flat env keys honored during the deprecation window.
- Secrets only as `${VAR}`; literal-secret warning; masked in audit log.
