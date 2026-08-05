---
date: 2026-05-14 PHASE-LOCK PT
ver: 2.0.0
author: Sliither
model: claude-opus-4-7
tags: [proxy, profiles, deferred, rejected, addendum]
---

# Universal LLM Proxy with Profile Routing — Future Plans and Rejected Items

## Purpose of this document

The initial draft of `future-plans.md` listed eight deferred items and nine rejected items. On re-evaluation under the lens of "if a feature adds significant value and the only cost is time, reintegrate it for the ship-ready product," most deferred items folded back into `requirements.md` and `design.md`. The result: this document is much shorter than its predecessor. It now lists only one genuinely deferred item (where the cost is complexity risk, not time) and the rejected items whose rationale rests on architectural conflict rather than time-economy.

The structure mirrors the original: Section A is deferred-with-trigger, Section B is rejected-with-rationale. Anyone proposing to reintegrate a Section B item should first re-read the rationale and identify which premise has changed.

---

## Section A: Deferred Items

### A.1 Multi-tool web-search dispatch with response splicing

**Description.** When a request invokes a web-search tool alongside other tools in the same turn, intelligently split the dispatch so that the web-search invocation runs on the profile's `web_search` slot model while the other tool calls run on the profile's `default` slot model, then splice the responses into a single coherent reply to the client.

**Why deferred and not reintegrated.** Unlike the Section A items that were folded back into the ship-ready spec, this one is deferred because the cost is not time alone; it is genuine complexity risk. Splicing model outputs across two upstream calls requires preserving response context invariants that LLMs depend on: that the model can see every tool it was offered, that its response reflects an unbroken reasoning chain, and that downstream tool-use turns receive the right tool-call IDs. Naive splicing can produce hallucinated tool calls (the search-handling model invents fictitious results from the other tool's context) or broken tool-call ID chains (the main model expects an ID the search model never produced).

The current rule (rewrite only when web-search is the only tool invoked in the turn or is explicitly forced via `tool_choice`) handles the dominant traffic pattern in pi, opencode, and other managed CLIs without any of these risks. Multi-tool turns containing both web-search and other tools are rare enough that the simple rule loses very little in practice.

**Trigger condition for revisit.** When traffic analysis (from the analytics surface that ships in v2.0) shows a non-trivial fraction of web-search turns also carrying other tools, AND when the resulting dispatch under the simple rule is observably wrong in cost or capability metrics, the splicing case becomes worth implementing. Until that pressure is concrete and measurable, the simple rule wins.

**Implementation sketch when revisited.** A "compound dispatcher" that constructs two upstream calls from a single client request, with explicit assistant message synthesis between them to ground the second call in the first's output. Requires a new test-corpus class covering tool-call ID continuity, request/response message ordering, and streaming reconstruction.

---

## Section B: Rejected Items

Each rejected item describes the capability declined, the architectural conflict it created, and (where applicable) the only circumstance in which a future maintainer should consider revisiting.

### B.1 Filesystem-watcher hot-reload

**Description.** Use the `watchfiles` library, `chokidar`, or Bun's native FSWatcher to detect changes to `profiles.json` and `providers.json` and reload automatically via observer callbacks, rather than checking mtime on each profile resolution.

**Architectural conflict.** A filesystem watcher introduces a runtime dependency, a background task that must be supervised across the proxy's lifecycle, and a set of failure modes (watcher death from filesystem semantics that vary across host OSes and containers, missed events on rapid edits, double-fire on editor save-rename patterns) that the mtime check trivially avoids. The mtime check is a single `Bun.stat()` call per profile resolution, comfortably under the 2-millisecond P99 budget, with zero failure modes that the proxy cannot recover from on the next request.

**Conditions to revisit.** None foreseeable. The mtime check is functionally equivalent for the registry's expected edit frequency. A watcher would only be justifiable if the proxy ran on a filesystem with non-trivial `stat` cost or unreliable mtime semantics, neither of which describes any realistic deployment.

### B.2 Profile inheritance via explicit `_inherits` chains

**Description.** Allow a profile to declare `_inherits: <other_profile>` and have its definition merged onto that profile's resolved overlay, supporting multi-level inheritance chains.

**Architectural conflict.** The implicit `default` overlay already covers the only inheritance case that appears in real registries: every profile is "default plus my deltas." Adding multi-level inheritance forces every implementation detail that the chosen design avoids: cycle detection, resolution ordering rules, debugging UX for "why did this profile end up with this value," documentation explaining how chains compose. The cost is permanent maintenance burden; the benefit is hypothetical convenience for a multi-user scenario the product does not support.

**Conditions to revisit.** If the product ever expands to a multi-user or multi-team scenario where three or more profiles share a non-default common base, and the registry duplication of that common base becomes a real maintenance problem. Until then, inheritance is YAGNI.

### B.3 Header-based profile selection (`X-Proxy-Profile`)

**Description.** A custom HTTP header that selects the profile for a request, allowing path-based and header-based selection to coexist.

**Architectural conflict.** None of the CLIs the product targets (pi, opencode, hermes, claude-code, codex) expose a native mechanism for injecting custom headers into upstream requests. A wrapper script that injects headers would have to wrap every CLI individually, multiplying alias-installation complexity. The path-based mechanism is uniformly supported via `BASE_URL` and `ANTHROPIC_BASE_URL` environment variables. Adding header-based selection means maintaining two mechanisms for the same purpose with no concrete consumer for the second.

**Conditions to revisit.** When a CLI under management gains native header-injection support AND an operational use case appears that benefits from header-form selection (such as inline profile switching during a session, which none of the current CLIs support). Both conditions are unlikely.

### B.4 Model-name-prefix profile encoding (`pi::qwen/qwen3-next-80b`)

**Description.** Encode the profile name into the model parameter (`profile_name::actual_model_name`), parsed and stripped by the proxy.

**Architectural conflict.** Pollutes the model namespace. Some CLIs validate model names against known lists and reject prefixed forms. Aliases would have to dual-purpose their model argument to carry both profile selection and the real model name. Logs and dashboards would have to special-case the encoding to display readable model names. None of these problems exist with path-based selection.

**Conditions to revisit.** When a deployment environment uniquely forces the proxy to expose only a single URL endpoint (e.g., behind a fixed reverse proxy whose path cannot be reconfigured), this could be a viable fallback. The condition is hypothetical enough that revisiting is purely defensive thinking.

### B.5 Triple-hop resolution (path + header + model-name-prefix, in priority order)

**Description.** Resolve the active profile by checking URL path prefix, then `X-Proxy-Profile` header, then model-name prefix, falling through to `default` if none match.

**Architectural conflict.** This is the union of three mechanisms, two of which (B.3, B.4) are independently rejected. Triple-hop adds resolution complexity, makes the active profile less predictable from a request's surface form, and creates real ambiguity when a request specifies multiple methods that disagree. Path-based alone is unambiguous and uniformly supported.

**Conditions to revisit.** Only if both B.3 and B.4 are independently revisited and accepted. Triple-hop is a consequence of accepting both, not an independent decision.

### B.6 Default profile synthesis when registry exists but is missing the `default` key

**Description.** When `profiles.json` exists but does not contain a `default` profile, synthesize one from the proxy's current global slot configuration rather than failing at startup.

**Architectural conflict.** Fail-fast on missing `default` makes the registry's invariants explicit and forces the operator to acknowledge that the registry is the source of truth. Silent synthesis hides registry-authoring mistakes and produces inconsistent behavior when the synthesized values drift from the operator's mental model. The lenient case is "no file at all" (covered by FR-072, which synthesizes from global config), which is the legitimate upgrade and first-launch path. Once the file exists, its content is authoritative.

**Conditions to revisit.** None foreseeable. The asymmetry between "no file" (synthesize) and "file present but missing default" (error) serves operator clarity.

### B.7 Environment-variable interpolation in profile values

**Description.** Allow profile slot values and other fields to reference environment variables (e.g., `"default": "${PROXY_DEFAULT_MODEL}"`) expanded at registry-load time.

**Architectural conflict.** Profiles are meant to be the source of truth for per-CLI routing. Interpolation introduces indirection that complicates debugging: when a request dispatches unexpectedly, the operator must check both the registry and the environment to understand why. Environment-driven configuration is the right primitive for proxy-wide settings (already supported via `PROXY_*` env vars); profile-specific values should be explicit.

**Conditions to revisit.** If profiles ever need to embed secrets (e.g., per-profile API keys when multi-account routing lands, though that capability is currently delivered via `provider_override` pointing at distinct configured providers, each with its own token), a dedicated secret-reference syntax (`@secret(key)`) would be cleaner than generic env-var interpolation. The need for either form is conditional on use cases not currently planned.

### B.8 Dedicated profile-management binary distinct from the unified CLI

**Description.** A separate binary (e.g., `proxy-profile-mgr`) for profile authoring, distinct from the main proxy binary.

**Architectural conflict.** The product ships as a single binary by design; introducing a second binary multiplies installation surface, distribution channels, and discoverability problems. The unified CLI's `proxy profile` subcommand family covers every profile-management operation and shares the service layer with the TUI and WebUI configurators.

**Conditions to revisit.** None foreseeable. The single-binary design is a core distribution principle.

### B.9 Caching of LLM responses for cost reduction

**Description.** Cache LLM responses keyed by request content hash, returning cached results to identical subsequent requests.

**Architectural conflict.** LLM response caching introduces correctness risks at multiple layers: tool-call result determinism (a cached web-search result is stale by definition), conversation-state implicit memory (LLMs trained with thinking tokens or hidden state may not produce identical outputs for identical inputs), and operator expectations that responses reflect current model behavior. The complexity of getting caching right correctly exceeds the value at this scope. Operators wanting caching can layer a separate caching proxy in front of this product.

**Conditions to revisit.** When a specific class of cacheable request (such as deterministic structured-output tool calls with documented determinism guarantees) becomes large enough in observed traffic to justify the implementation. The required prerequisites are mature determinism contracts from upstream providers that do not currently exist for most models.

### B.10 Hosted SaaS deployment of the proxy

**Description.** Operate the proxy as a multi-tenant cloud service that users connect to remotely.

**Architectural conflict.** The product is designed for single-operator local execution. Multi-tenancy adds authentication, authorization, isolation, billing, and operational surfaces that are not present in the design. The proxy's threat model assumes localhost trust; relaxing that assumption would require a different architecture from the ground up.

**Conditions to revisit.** Never as an extension of this product. A hosted SaaS version of the same concept would be a distinct product with a distinct codebase, sharing only the conceptual lineage.

---

## Closing note

Section A's single remaining item is deferred because its cost is complexity risk and correctness risk, not time. Reintegrating it under the new lens would violate the lens itself. Section B's items are not time-deferred; each represents an architectural decision that the project's intent depends on. The smaller size of this document compared to its predecessor reflects the rigor of the ship-ready lens: most items that previously hid under "deferred" were really just sequencing decisions that the new requirements correctly hoisted into the spec.

