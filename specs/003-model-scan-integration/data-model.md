# Data Model: Model-Scan Integration

Conceptual entities and live state. Schemas in `contracts/`. Implementation types in `design.md`
sections 3, 4.4, 4.11.

## Published contract entities (model-scan to router)

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| RoutingSnapshot | Versioned measured selection data for all roles | schema_version, generated_at, scan_id, blocklist, provider_health, provider_quota | contains many Role Selections |
| Role Selection | Per-role best model and ranked candidates | role id, label, eval_mode, best, candidates | within a Snapshot; bound to a Tier or use case |
| Candidate | One scored model option | api_model, provider, base_url, fitness, price_blended, tier, has_tools, has_vision | listed in a Role Selection; may enter a Cascade |
| Quota State | Per-provider quota window state | remaining_fraction, reset_at, unit, best_tier_available, source | within a Snapshot; feeds Rotation |

## Router runtime entities

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| Selection Policy | Rule for choosing among candidates | kind (static/free/budget/quality/roles/rotate), price_ceiling | applied during Binding |
| Tier Assignment | A fixed router slot resolved to a model | tier, model, provider, cascade, source | produced by Binding from a Role Selection |
| Cascade | Ordered fallback models for a role | ordered model list | derived from a Role Selection minus blocklist and primary |
| Profile Binding | Per-tool mapping of tiers and use cases to roles | profile, tier-to-role map, overrides | overlays Tier Assignment for one tool |
| Lane | Consumption class with a policy and quota pool | name, policy, pool, free floor | assigned to a Preset or Session |
| Quota Ledger | Merged per-provider remaining quota | provider, remaining, reset, source precedence | feeds Rotation; built from QuotaSource adapters |
| Rotation State | Live interactive-primary selection state | active_provider per role, cooldowns | derived from Ledger and Snapshot |

## Launch and session entities

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| Preset | Curated named profile for one tool | tool, lane, default policy, per-role defaults | base layer for a Session |
| Session Config | Effective routing for one running tool instance | preset, policy, compress, provider_override, roles | composed into an Ephemeral Profile |
| Ephemeral Profile | Session-scoped profile at a unique address | id, url_prefix, overlay, ttl | created and removed per Session |
| Chain | Services a launch depends on | router, optional upstream proxy, compression stage and local model | brought up by one command |

## State transitions

- Binding: (Snapshot, Selection Policy, Profile Bindings) gives global Tier Assignments plus a
  per-profile overlay map; swapped atomically; provenance recorded per tier and role.
- Rotation: on quota-drain crossing or a 429, the interactive primary rebinds to the next paid
  provider, then to the free floor when the paid pool is spent; cooldowns prevent flapping.
- Session lifecycle: launch composes layers, registers an Ephemeral Profile, runs the tool;
  exit deregisters; a TTL sweep reclaims orphans.
- Degradation: missing, stale, or incompatible Snapshot retains the last good binding or the
  static config; no binding is ever emptied.

## Validation rules

- Candidate.price_blended null is ineligible for budget and free policies, eligible for quality.
- A blocklisted model never appears as a primary or in a cascade.
- A role absent from the Snapshot keeps its static value.
- The Snapshot contains no credentials; provider base_url and key resolve from the router
  registry, honoring a snapshot base_url only for a provider already trusted.
- Quota Ledger functions from internal adapters alone when all external sources are absent.
