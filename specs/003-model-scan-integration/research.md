# Research: Model-Scan Integration

Phase 0 decisions and rationale. Full prior-art table in `requirements.md` section 8.

## Decision: file contract over request-time API

- Decision: model-scan publishes a versioned `routing_snapshot.json`; the router reads it at
  startup, SIGHUP, TTL, and on explicit refresh. A live gateway pull exists for admin only.
- Rationale: a request-time call would add latency and a hard runtime dependency to the hot path
  and couple the two projects' lifecycles. A versioned file decouples by data, survives the
  engine being offline, and is cacheable in memory.
- Alternatives rejected: request-time gateway call (hot-path dependency); shared database
  (tighter coupling, lifecycle entanglement).

## Decision: cascade from the snapshot

- Decision: each role's ranked candidates (minus blocklist and primary) become the Assignment
  cascade.
- Rationale: every cascade is empty today; model-scan already ranks candidates. This is the
  single highest-value change and makes fallback availability-aware for the first time.

## Decision: per-profile slot bindings as an overlay

- Decision: a `slot_bindings` map per profile, global default plus overrides, applied as an
  overlay after tier resolution, mirroring the existing `tier_overrides`.
- Rationale: reuses the established overlay precedence and keeps profile concerns in the profile
  file. Per-profile tier bindings that differ from default are precomputed into an in-memory
  overlay because the registry holds one global value per tier.

## Decision: native rotation on the existing substrate; tokscale primary behind an adapter

- Decision: build quota-aware rotation native in the router, consuming the existing
  `rate_limiter`, `usage_tracker`, and `billing_integrations`. Ingest external subscription quota
  through a pluggable `QuotaSource` adapter with tokscale primary and ccusage secondary. Adopt
  gpt-load's rotate-on-429 pattern natively. Reject gpt-load and LiteLLM as components.
- Rationale: the router is already the chokepoint that observes every request and 429 and runs
  cascade and circuit-breaker logic; adding another rotation proxy would duplicate it and add a
  hop, breaking the single chain. tokscale covers the operator's actual tool set far more
  completely than ccusage (20+ tools vs six, including Antigravity, Gemini, Qwen, Kiro, OpenCode),
  with a queryable SQLite; the adapter interface insulates the ledger from tokscale's schema and
  keeps ccusage as a stable-contract secondary. The proxy already has a quota substrate, so this
  is new feature work built on it, not greenfield.
- Alternatives rejected: gpt-load proxy (duplicates routing, adds a hop); LiteLLM proxy (heavy,
  second proxy); ccusage-only feed (too narrow for the operator's stack); tokenusage and
  coding_agent_usage_tracker (narrower monitors).

## Decision: free floor instead of a paid reserve

- Decision: when the paid pool drains, the interactive primary falls to the best free model (a
  configurable preferred default, deepseek-v4-flash, unless the engine ranks a better free
  S-tier such as an OpenRouter stealth model higher), not a held-back paid provider.
- Rationale: the operator does not want a paid backup; falling to best-free never blocks and
  never forces a paid call once paid quota is spent, while still maximizing weekly paid
  utilization before the floor.

## Decision: lanes for the free-vs-S-tier split

- Decision: a `standby` lane (free only) for 24/7 agents and an `interactive` lane (quota-aware
  S-tier rotation) for CLI tools; presets declare a lane, sessions may override.
- Rationale: cleanly guarantees 24/7 agents never spend premium quota and that toolcalling stays
  free, while interactive tools maximize S-tier utilization.

## Decision: session-scoped ephemeral profiles

- Decision: the launcher composes preset, session file, and inline args into one overlay, and
  registers it as an ephemeral profile at a unique address, removed at session end.
- Rationale: profile-scoped routing cannot serve two sessions of one tool with different configs;
  ephemeral profiles can, with no global config edit. The existing session correlation id becomes
  the observability key.

## Decision: keep the projects separate; reuse the existing constitution

- Decision: contract-only coupling; neither project imports the other. The existing ratified
  project constitution governs this feature; it is not regenerated.
- Rationale: each project is independently useful; the coupling surface stays minimal and
  versioned.

## Decision: `api_model` derivation rule (producer side, model-scan)

- Decision: model-scan is the single authority for the snapshot's `api_model` field — the
  router-ready identifier the consumer binds without reinterpretation. The derivation is:
  `api_model = f"{provider}/{model_id}"`, where `provider` is the registry-canonical provider
  name and `model_id` is the provider-native id exactly as the upstream expects it (including any
  vendor namespace and reachability suffix, e.g. `deepseek/deepseek-v4-flash:free` or
  `qwen3-coder-next:cloud`). model-scan does not strip, lowercase, or otherwise normalize the
  native id; the suffix that made the model reachable in the scan is the suffix the router must
  send. When the provider name is already embedded in `model_id` by the upstream's own
  convention, model-scan still prefixes the registry provider so the consumer parses a single
  consistent `provider/native_id` shape (the consumer splits on the first `/`).
- Rationale: behavior-driven, not an allowlist — the scan observed the exact id that worked, so
  the contract carries that observed id rather than a reconstructed guess. Centralizing derivation
  in the producer keeps the consumer free of provider-format special-casing and means a new
  provider needs no router code change. `model_id` and `provider` remain in the candidate for
  provenance and for the router's registry lookup; `api_model` is the bind target.
- Alternatives rejected: router re-derives `api_model` from `model_id` + `provider` (duplicates
  provider-format knowledge on both sides, drifts); a bare `model_id` without provider prefix
  (forces the consumer to guess the registry key).

## Decision: `base_url` gap-fill rule (consumer side, router)

- Decision: `base_url` in a candidate is advisory and frequently empty. The router fills any
  empty (or absent) `base_url` from its own provider registry keyed by the candidate's `provider`
  at bind time. A non-empty `base_url` in the snapshot wins only when the router's registry has no
  entry for that provider (the snapshot's endpoint is then the sole source); when both are
  present, the router registry is authoritative because it owns credential-paired endpoints. The
  snapshot never carries credentials, so a snapshot `base_url` is an endpoint hint only and is
  never paired with a key from the contract.
- Rationale: endpoints belong with the credentials that authenticate them, and those live only in
  the router's registry (No Secrets in Git-Tracked Files; credential loading order untouched). The
  producer should not need to know the router's deployment topology. Gap-fill lets model-scan emit
  `base_url: ""` for every known provider and only populate it for a provider the router does not
  yet know, which the router surfaces rather than silently dropping.
- Alternatives rejected: snapshot `base_url` always wins (would let a diagnostic artifact override
  the credential-paired endpoint, risking an authenticated request to the wrong host); require
  model-scan to always populate `base_url` (couples the producer to router deployment detail and
  invites credential/endpoint mismatch).

## SPIKE: tokscale schema and provider key pool

- Finding: the router did not have a per-provider key pool before this pass. Provider registry
  values were single-key (`PROVIDERS_<name>_API_KEY`) plus endpoint. The implementation now also
  reads optional comma-separated `PROVIDERS_<name>_API_KEYS` and can rotate once on a 429 before
  cascading.
- Finding: tokscale integration is intentionally adapter-based. The adapter expects a normalized
  SQLite table named `provider_quota(provider, remaining_fraction, reset_at, unit)`. If a local
  tokscale install uses a different raw schema, the shim belongs in `TokscaleSQLiteSource`, not in
  the router hot path.
- Resolution path: quota sources normalize to `QuotaSample`; merge precedence is tokscale,
  ccusage, model-scan quota, billing, rate limiter, usage tracker. The rotation layer consumes the
  merged provider map only.
