---
date: 2026-05-14 PHASE-LOCK PT
ver: 1.0.0
author: Sliither
model: claude-opus-4-7
tags: [proxy, profiles, deferred, rejected, addendum]
---

# Profile Routing for claude-code-proxy — Future Plans and Rejected Items

## Purpose of this document

The Option C+ assessment that preceded this design proposed a more expansive feature set than Option C-slim shipped. Several capabilities from that assessment were deferred to future phases rather than rejected outright; others were rejected entirely because they solve no current problem or because they conflict with the project's architectural intent. This document records both categories so that future decision-makers can locate the reasoning when concrete pain emerges.

The document is structured in two sections. The first lists items that are deferred but expected to be implemented when specific triggering conditions occur. The second lists items that are rejected for this project entirely; if a future maintainer believes one of these should be revisited, the rationale here is the starting point for the conversation.

---

## Section A: Deferred Items

Each deferred item describes the capability, the reason it is not in the initial implementation, and the triggering condition that would justify revisiting it.

### A.1 Dashboard read-only display of resolved profile overlays and per-profile request counts

**Description.** The web dashboard would surface, for each defined profile, the resolved overlay (the profile's values merged onto `default`) and the count of requests served through that profile over a rolling 24-hour window.

**Why deferred.** The initial implementation must validate end-to-end before investing in UI work. Until profiles are observably useful in operation, the dashboard work risks shipping a UI for an under-used feature.

**Trigger condition.** When at least three profiles are in regular daily use and operators ask whether profile X is being hit, the dashboard surface becomes worth its build cost. This is targeted for Phase 3 of the implementation phases in `design.md`.

### A.2 `proxies profile` CLI subcommands

**Description.** Three new subcommands on the existing `proxies` CLI: `proxies profile list` (enumerate profiles), `proxies profile show <name>` (print the resolved overlay), and `proxies profile validate` (check that every profile's model identifiers resolve through the proxy's provider system).

**Why deferred.** The initial implementation makes profile authoring direct (edit the JSON file), and JSON is small enough that hand-validation is feasible. The CLI surface adds operator convenience but is not a blocking gap.

**Trigger condition.** When profile-validation errors begin appearing in logs because operators are mistyping model identifiers, the `validate` subcommand pays for itself. Targeted for Phase 3.

### A.3 Per-profile provider-override

**Description.** An optional `provider_override` field on a profile that names a specific entry from the proxy's `config/proxy_chain.json` (or its successor). When present, requests through that profile route exclusively to that provider rather than following the global provider order.

**Why deferred.** No current use case requires per-profile provider selection; all profiles target the same OpenRouter-cascade backend. However, the schema must remain forward-compatible because the inevitable next feature is per-account OAuth routing (claude-code-switch style), which needs exactly this capability.

**Trigger condition.** When the proxy gains multi-account OAuth support (e.g., multiple Claude Max accounts, multiple OpenRouter accounts), profile-level provider selection becomes the natural binding. Targeted for Phase 4.

### A.4 Per-profile cascade chain customization

**Description.** Allow a profile to specify a complete cascade chain (ordered model fallback list) distinct from the global cascade behavior, beyond the per-slot override currently supported.

**Why deferred.** The existing cascade-and-circuit-breaker machinery applies uniformly within a slot's resolution; if a profile overrides a slot, the cascade still runs against the substituted model. This covers the common case. Custom cascade ordering per profile is a deeper customization with no current consumer.

**Trigger condition.** When two profiles need genuinely different fallback chains (e.g., one wants speed-prioritized fallbacks and another wants cost-prioritized fallbacks), this becomes worth implementing. Until that pressure exists, the per-slot override is sufficient.

### A.5 Web-search interception for multi-tool turns

**Description.** Extend the web-search interceptor to handle turns in which a web-search tool is invoked alongside other tools, intelligently splitting the dispatch so that web-search reasoning runs on the `web_search` slot's model while the other tool calls remain on the profile's `default` slot model.

**Why deferred.** The current pattern in pi and most other CLIs is single-tool turns. Multi-tool turns with web-search alongside other tools are rare enough that the current "only if web-search is the only tool, or if explicitly forced" rule covers nearly all real traffic. Implementing the split-dispatch case requires significant request-rewriting complexity and risks breaking the assumption that a model's response context contains all the tools it was invited to use.

**Trigger condition.** When traffic analysis shows a non-trivial fraction of web-search turns also carrying other tools and the wrong dispatch is observable in cost or capability metrics, the case for split-dispatch becomes concrete. Until then, the simple rule wins on maintenance cost.

### A.6 Profile-level temperature and max-tokens overrides

**Description.** Allow profiles to override request parameters like `temperature`, `max_tokens`, `top_p`, etc., for all dispatches in their context.

**Why deferred.** These parameters are typically set per-request by the client, and overriding them at the profile layer risks confusing clients that expect their parameters to be honored. The schema is forward-compatible (unknown fields are ignored), so adding this later is non-breaking.

**Trigger condition.** When a use case emerges in which a CLI consistently sends inappropriate parameter values that the proxy should normalize per profile, this becomes useful. The classic example would be a CLI hardcoding temperature 1.0 for code generation when temperature 0.2 would produce better results.

### A.7 Profile usage analytics: cost breakdown and latency distributions

**Description.** Per-profile dashboards showing cost over time, latency P50/P95/P99, and per-slot model utilization within each profile.

**Why deferred.** The proxy already has comprehensive usage tracking; adding profile as a column (Phase 3) enables future analytics builds with no schema rework. The dashboards themselves are pure value-add and can be assembled when operators want them.

**Trigger condition.** When the user begins making cost or model-selection decisions based on per-profile data and wants the proxy to surface it rather than running ad-hoc SQL queries against the usage database.

### A.8 OpenAPI / dashboard reflection of available profile paths

**Description.** Auto-generate OpenAPI specs and dashboard route documentation that reflect every defined profile's available paths, rather than documenting only the legacy paths.

**Why deferred.** Profile paths are deterministic from the registry contents; clients can construct them directly. Auto-reflection adds value for discoverability but is not blocking.

**Trigger condition.** When external integrators or documentation generators need a machine-readable list of available profile endpoints.

---

## Section B: Rejected Items

Each rejected item describes the capability proposed in Option C+ that this design declines to implement, the rationale for rejection, and the conditions (if any) under which the rejection should be revisited.

### B.1 Filesystem-watcher hot-reload

**Description.** Use the `watchfiles` library (or a similar async filesystem-watcher) to detect changes to `profiles.json` and reload it automatically, rather than checking mtime on each profile resolution.

**Rejection rationale.** A filesystem watcher introduces a runtime dependency, a background thread or task that must be managed across the proxy's lifecycle, and a set of failure modes (watcher death, missed events, filesystem semantics that vary across host OSes and containers) that the mtime check trivially avoids. The mtime check is one `os.stat` call per request that resolves a profile; this cost is comfortably under the 1-millisecond P99 budget and adds zero failure modes. The mtime approach also recovers automatically from any filesystem oddity because every request independently checks the current state.

**Conditions to revisit.** None foreseeable. The mtime check is functionally equivalent for the registry's edit frequency (single-digit edits per day at most). The watcher would only be justifiable if the proxy ran on a filesystem where `os.stat` had non-trivial cost or unreliable mtime semantics, neither of which describes any realistic deployment.

### B.2 Profile inheritance via explicit `_inherits` keys

**Description.** Allow a profile to declare `_inherits: <other_profile>` and have its definition merged onto that profile's resolved overlay, supporting multi-level inheritance chains.

**Rejection rationale.** The implicit `default` overlay handles the only inheritance case that actually appears in observed registries: every profile is conceptually "default plus my deltas." Adding multi-level inheritance requires cycle detection, resolution ordering rules, and documentation for users about how chains compose. The cost is real maintenance burden; the benefit is zero for the observed use case. If a future use case emerges that needs three-level inheritance (e.g., a `team-default` between `default` and individual user profiles), the inheritance system can be added then with explicit motivation. Adding it speculatively is YAGNI.

**Conditions to revisit.** When a concrete use case emerges in which three or more profiles share a non-default common base, and the registry duplication of that common base becomes a maintenance problem. This is most likely to happen if the proxy is ever deployed in a multi-user context.

### B.3 Header-based profile selection (`X-Proxy-Profile: pi`)

**Description.** A custom HTTP header that selects the profile for a request, allowing path-based and header-based selection in parallel.

**Rejection rationale.** No CLI under management (pi, opencode, hermes, claude-code, codex) exposes a native mechanism for injecting custom headers into upstream requests. A wrapper script that injects the header would have to wrap every CLI individually, multiplying the alias-installation complexity. The path-based mechanism is uniformly supported via `BASE_URL` / `ANTHROPIC_BASE_URL` env vars across every CLI under management. Adding header-based selection means maintaining two mechanisms for the same purpose with no concrete consumer for the second one.

**Conditions to revisit.** When a CLI under management gains native header-injection support, and an operational use case appears that benefits from the header form (such as inline profile switching during a session, which none of the current CLIs support anyway). Until both conditions are met, paths suffice.

### B.4 Model-name-prefix profile encoding (`pi::qwen/qwen3-next-80b`)

**Description.** Encode the profile name into the model parameter (`profile_name::actual_model_name`), stripped and parsed by the proxy.

**Rejection rationale.** This pollutes the model namespace; some CLIs validate model names against a known list and would reject prefixed names; aliases would have to dual-purpose their model arg to carry both the profile selection and the actual model name; the encoding is non-obvious to humans reading logs or configuration. Path-based selection has none of these problems.

**Conditions to revisit.** When a deployment environment uniquely forces the proxy to expose only a single URL endpoint (e.g., behind a fixed reverse proxy path that cannot be re-configured), this could be a viable fallback. The conditions are unusual enough that revisiting is hypothetical.

### B.5 Dedicated profile-management binary or interactive TUI

**Description.** A separate `proxy profiles` binary or TUI for creating, editing, validating, and templating profiles.

**Rejection rationale.** The existing `proxies` CLI is the natural home for any profile-management subcommands (deferred to Section A.2). A separate binary multiplies installation surface and discoverability problems. An interactive TUI for profile authoring is over-engineered: profiles are short JSON snippets that are faster to edit in any text editor than to navigate through a TUI workflow.

**Conditions to revisit.** None foreseeable. The TUI form factor is wrong for the data shape; profiles will never be complex enough to justify it.

### B.6 Generated profile templates for known CLIs

**Description.** A command like `proxies profile init --template pi` that generates a starter profile entry with sensible defaults derived from knowledge of pi's tool-call patterns.

**Rejection rationale.** The starter registry already includes seed profiles for the five CLIs under management. New CLIs are added rarely enough that hand-authoring the profile entry is faster than building, documenting, and maintaining a template system. The seed profiles in the initial `profiles.json` serve the same purpose with zero code.

**Conditions to revisit.** If the project ever supports a long-tail of CLIs (dozens) where each has CLI-specific tool-call patterns that map to specific slot overrides, templates would amortize the per-CLI authoring cost. The current project scope makes this unlikely.

### B.7 Triple-hop resolution (path + header + model-name-prefix, in priority order)

**Description.** Resolve the active profile by checking, in order: URL path prefix, then `X-Proxy-Profile` header, then model-name prefix, then falling back to `default`.

**Rejection rationale.** This is the union of three mechanisms, two of which are independently rejected (B.3 and B.4). The triple-hop fallback adds resolution complexity, makes the active profile less predictable from a request's surface form, and creates ambiguity when a request specifies multiple methods that disagree. Path-based selection alone is unambiguous and uniformly supported.

**Conditions to revisit.** Only if both B.3 and B.4 are individually revisited and accepted. The triple-hop machinery is a consequence of accepting both, not an independent decision.

### B.8 Synthesizing a `default` profile from existing global config when the registry is missing the `default` key

**Description.** When `profiles.json` exists but does not contain a `default` profile, synthesize one from the proxy's current global slot configuration rather than failing at startup.

**Rejection rationale.** Fail-fast on missing `default` makes the registry's invariants explicit and forces the operator to acknowledge that the registry is the source of truth for profile resolution. Silent synthesis hides registry-authoring mistakes and can lead to inconsistent behavior when the synthesized values drift from the operator's mental model. The slightly more lenient case is `profiles.json` not existing at all (FR-041 accepts this and synthesizes default from global config), which is the upgrade path. Once the file exists, its content is authoritative.

**Conditions to revisit.** None foreseeable. The asymmetry between "no file" (synthesize) and "file present but missing default" (error) is intentional and serves operator clarity.

### B.9 Inheriting environment variables into profile slot values via `${VAR}` interpolation

**Description.** Allow profile slot values to reference environment variables, e.g., `"default": "${PROXY_DEFAULT_MODEL}"`, expanded at registry-load time.

**Rejection rationale.** Profiles are meant to be the source of truth for per-CLI routing. Interpolation introduces an additional layer of indirection that complicates debugging: when a request dispatches to the wrong model, the operator must check both the registry and the environment to understand why. Environment-driven configuration is the right primitive for proxy-wide settings (already in `.env`); profile-specific settings should be explicit in the registry file.

**Conditions to revisit.** If profiles ever need to embed secrets (such as upstream API keys, when per-profile provider override lands per A.3), interpolation from a secrets store may become necessary. Even then, dedicated secret-reference syntax (`@secret(key)`) is cleaner than generic env-var interpolation.

---

## Closing note

The deferred items in Section A are all expected to be implemented in some form when their trigger conditions appear. The rejected items in Section B are not expected to be implemented unless the architectural intent of the project changes, which would itself be a larger conversation than reopening any single rejected item. Anyone proposing to add a Section B item should first re-read the rejection rationale and explicitly identify which premise has changed.

