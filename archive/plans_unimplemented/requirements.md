---
date: 2026-05-14 PHASE-LOCK PT
ver: 2.0.0
author: Sliither
model: claude-opus-4-7
tags: [proxy, profiles, routing, cli, tui, webui, analytics, requirements]
---

# Universal LLM Proxy with Profile Routing — Requirements Specification v2.0

## 1. Purpose

This product is a standalone local proxy that sits between command-line AI tools (such as pi, opencode, hermes, claude-code, codex) and upstream LLM providers (OpenRouter, Anthropic, OpenAI, local models). The proxy translates between the OpenAI Chat Completions wire format and the Anthropic Messages wire format, routes requests through a cascade of upstream models with automatic fallback on failure, and isolates failing models behind a circuit breaker. On top of those core proxy capabilities, the product adds per-request profile routing: each connected CLI tool selects an independent bundle of model overrides per slot role (default, background, think, long context, image, web search) without affecting other tools running against the same proxy instance.

The product exposes three first-class configuration surfaces so that users can choose their preferred ergonomics: a scriptable command-line interface with arguments, an interactive terminal user interface with keyboard navigation, and a browser-based web user interface. The web surface additionally presents both historical analytics and a real-time request stream, with cost tracking, latency distributions, error rates, token consumption, per-profile rollups, and a circuit-breaker health board.

The product ships as a single distributable artifact and runs as a single process. It does not depend on any external proxy, gateway, or routing service. It is designed for personal and small-team workflows where one operator runs multiple AI tools concurrently against a shared backend.

## 2. Glossary

| Term | Definition |
|------|-----------|
| **Slot** | A named role consumed by the request handler when selecting which model to dispatch. Recognized slots: `default`, `background`, `think`, `long_context`, `image`, `web_search`. |
| **Profile** | A named bundle of overrides stored in the profile registry. Each profile may override any slot, the cascade chain, the upstream provider, request parameters such as temperature and max tokens, and web-search interception behavior. |
| **Profile Registry** | The persistent file (`profiles/profiles.json`) that holds the complete set of defined profiles. |
| **Overlay** | The merge operation that produces a request's effective configuration by applying a profile's values onto the `default` profile's values. |
| **Profile Path** | A URL prefix of the form `/p/{profile-name}/v1/...` that selects which profile applies to a request. |
| **Upstream Provider** | An LLM service or local endpoint reachable by the proxy (OpenRouter, Anthropic, OpenAI, Ollama, llama.cpp, etc.). |
| **Cascade Chain** | An ordered list of model identifiers that the proxy attempts in sequence when a slot's primary model fails or is circuit-broken. |
| **Circuit Breaker** | The mechanism that marks a model as temporarily unavailable after a threshold of failures and bypasses it during cascade resolution until the cooldown elapses. |
| **Web-Search Interception** | The runtime pattern in which the proxy detects a web-search tool invocation, rewrites the model field to the profile's `web_search` slot value, and dispatches the rewritten request. |
| **Request Record** | The persistent log entry written for every served request, carrying timing, token counts, cost estimate, profile, slot, dispatched model, and outcome. |
| **Configurator** | Any of the three first-class interfaces for editing the proxy's configuration: the CLI, the TUI, the WebUI. |

## 3. User Scenarios

### 3.1 Primary User Story

As a power user running multiple AI coding assistants in parallel terminal sessions, I want each tool to use its own bundle of model configurations across all task roles, with a single proxy instance serving them all, plus the ability to monitor my spending and latency in real time and tune any profile through whichever configurator (command line, terminal UI, or browser) fits the moment.

### 3.2 Acceptance Scenarios

**Scenario 1: Five tools, five profiles, one proxy**
- Given: The proxy is running with five profiles defined.
- When: The operator opens five terminals and launches pi, opencode, hermes, claude-code, codex concurrently, each via its profile-specific alias.
- Then: Each tool's requests route through its profile's slot configuration. The dashboard shows five distinct profile activities concurrently. No tool's configuration affects any other tool.

**Scenario 2: Web-search interception swaps the model**
- Given: A profile defines a `web_search` slot value distinct from its `default`.
- When: A request from that profile invokes a web-search tool as the only tool in the turn.
- Then: The proxy dispatches the swapped model. The substitution event appears in the request record and the real-time stream highlights it.

**Scenario 3: Real-time spend visibility**
- Given: The web dashboard is open in a browser and the proxy is serving traffic.
- When: A new request completes upstream.
- Then: Within one second the dashboard's real-time stream shows the request and the running cost counters update without a page reload.

**Scenario 4: Configure a new profile via CLI**
- Given: The proxy is running with no profile named `local-llama`.
- When: The operator runs `proxy profile create local-llama --template ollama --slot default=ollama/qwen3-coder-32b`.
- Then: The profile is created, validated, persisted to `profiles/profiles.json`, and immediately available for routing at `/p/local-llama/v1/...` with no restart.

**Scenario 5: Configure a new profile via TUI**
- Given: The operator launches the TUI with `proxy tui`.
- When: The operator navigates to Profile Manager, presses `n` for new, selects a template from a list, fills in slot overrides via keyboard-driven forms, and presses `s` to save.
- Then: The profile is persisted with the same validation as the CLI path. The TUI returns to the profile list showing the new entry.

**Scenario 6: Configure a new profile via WebUI**
- Given: The operator opens the web dashboard's Profile Manager.
- When: The operator clicks "New Profile," picks a template from a dropdown, edits fields in a form, and clicks Save.
- Then: The same persistence and validation as the other two configurators applies. The browser shows the new profile in the list and the JSON preview reflects the saved state.

**Scenario 7: Historical analytics**
- Given: The proxy has been serving traffic for at least 24 hours.
- When: The operator opens the Analytics view in the web dashboard and selects a 7-day window grouped by profile.
- Then: The view renders a time-series chart of requests, a stacked-bar breakdown of tokens by slot, a latency-distribution chart (P50/P95/P99), a cost-by-model table, and an error-rate trend line.

**Scenario 8: Unknown profile is rejected**
- Given: A client targets a profile path whose name is not defined.
- When: The request arrives.
- Then: The proxy returns a structured 404-class error naming the missing profile and listing the available profiles. No upstream call is made.

**Scenario 9: Circuit breaker activation**
- Given: An upstream model returns repeated errors above the configured failure threshold.
- When: A cascade resolution would normally select that model.
- Then: The model is bypassed for the duration of the cooldown. The TUI provider-health panel and the WebUI health board display the open circuit. The next successful probe transitions the circuit to half-open.

**Scenario 10: Live registry edit picked up without restart**
- Given: The proxy is running and serving requests.
- When: An operator edits `profiles/profiles.json` outside any configurator (direct file edit).
- Then: The next request that resolves a profile sees the updated content. In-flight requests are unaffected.

## 4. Functional Requirements

### 4.1 Request Handling and Protocol Compatibility

**FR-001**: The system SHALL accept POST requests at the OpenAI-compatible Chat Completions path and at the Anthropic-compatible Messages path, in both legacy form (`/v1/chat/completions`, `/v1/messages`) and profile-prefixed form (`/p/{profile}/v1/chat/completions`, `/p/{profile}/v1/messages`).
- Acceptance: All four path patterns return well-formed responses for valid requests. Path-prefix variants apply the named profile; legacy variants apply the `default` profile.

**FR-002**: The system SHALL translate between OpenAI and Anthropic request and response shapes such that a client sending in one wire format can dispatch upstream to a provider speaking the other format, with tool calls, streaming, and content blocks preserved correctly across translation.
- Acceptance: An OpenAI-format request to a model whose upstream provider is Anthropic returns an OpenAI-shaped response that round-trips through the client's parser. The same property holds in the reverse direction. Tool-call IDs, names, arguments, and result blocks survive both directions.

**FR-003**: The system SHALL support server-sent-event streaming responses for both protocol formats and SHALL preserve incremental token delivery from upstream through to the client.
- Acceptance: A streaming request shows token-level chunks arriving in the client's stream consumer with latency comparable to a direct upstream stream (less than 50 milliseconds of additional buffering at P95).

**FR-004**: The system SHALL forward all unknown request fields to the upstream provider unmodified, except where the proxy explicitly rewrites them (model field, system prompts when format translation requires it).
- Acceptance: Adding an arbitrary custom field to a request body produces the same upstream behavior as if the proxy were not in the path.

### 4.2 Upstream Provider Routing

**FR-010**: The system SHALL support multiple upstream providers, each defined by a name, a base URL, an authentication token, and a wire-format kind (openai-compatible, anthropic-compatible, ollama-compatible, custom).
- Acceptance: Adding a new provider to the configuration enables routing to that provider's models on the next profile resolution without restart.

**FR-011**: The system SHALL route a request to an upstream provider based on (a) the active profile's `provider_override` if defined, otherwise (b) a global provider preference order configured at the system level.
- Acceptance: A profile with `provider_override: "anthropic-direct"` routes its requests to the named provider regardless of the global order. A profile without the override follows the global preference.

**FR-012**: The system SHALL gracefully handle provider authentication failures by surfacing the error to the client with the upstream's status code and message, and by recording the failure in the request record without retrying through cascade (auth failures are not transient).
- Acceptance: A request to a provider with an invalid token returns the upstream's 401 with original error body. Cascade is not invoked for this class of failure.

### 4.3 Cascade and Circuit Breaker

**FR-020**: The system SHALL maintain a per-slot cascade chain. When a request's resolved slot model fails with a transient error (5xx, network timeout, rate limit), the proxy SHALL attempt the next model in the chain.
- Acceptance: Simulated failures on the primary model produce successful responses through the cascade with logged fallback events.

**FR-021**: The system SHALL allow profiles to override the cascade chain per slot via an optional `cascade` mapping of slot-name to ordered model list.
- Acceptance: A profile with `cascade.default: ["model-a", "model-b"]` uses that chain regardless of any global cascade configuration.

**FR-022**: The system SHALL implement a per-model circuit breaker that opens after a configurable threshold of consecutive failures within a sliding window, blocks dispatches to the affected model for a cooldown period, and probes with half-open state before fully closing again.
- Acceptance: Repeatedly failing a model 5 times within 60 seconds opens its circuit for 5 minutes. During the open period, cascade skips the model entirely. After cooldown, the next dispatch enters half-open; one success closes the circuit, one failure reopens it.

**FR-023**: The system SHALL expose circuit-breaker state via the analytics surface, including current state (closed/open/half-open), opened-at timestamp, expected cooldown end, and recent failure samples.
- Acceptance: Circuit-breaker events appear in real-time on the dashboard and in TUI provider-health panels.

### 4.4 Profile Registry

**FR-030**: The system SHALL maintain a profile registry file at a fixed location (`profiles/profiles.json` relative to the proxy's data directory) containing a top-level object keyed by profile name.
- Acceptance: A valid registry loads on startup. The `default` profile is mandatory; its absence is a startup-failing error.

**FR-031**: The system SHALL recognize the following fields on each profile entry: `default`, `background`, `think`, `long_context`, `image`, `web_search` (slot model identifiers); `cascade` (mapping of slot to ordered model array); `provider_override` (string naming a configured upstream provider); `web_search_intercept` (boolean defaulting true); `web_search_pattern` (regex string); `parameters` (mapping of request parameter to override value, recognized keys: `temperature`, `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`); `notes` (free-form string).
- Acceptance: Every recognized field is honored when set. Unknown top-level fields are preserved through reads and writes for forward compatibility but ignored for routing.

**FR-032**: The system SHALL re-read the registry file when its modification time has advanced since the last load, with no requirement for proxy restart or configurator intervention.
- Acceptance: An external edit to the registry is reflected on the next request that resolves a profile.

**FR-033**: The system SHALL preserve the last successfully parsed registry state in memory and SHALL continue serving with that state when a subsequent load encounters malformed JSON or a missing `default` entry, while emitting a warning-level log record.
- Acceptance: Corrupting the registry mid-flight does not crash the proxy or break in-flight requests; fixing the file restores normal reload behavior.

### 4.5 Profile-Based Request Routing

**FR-040**: The system SHALL extract the profile name from a request path of form `/p/{profile-name}/v1/...` and resolve it through the registry before dispatching the request.
- Acceptance: Requests to `/p/pi/v1/chat/completions` route through the `pi` profile context. Requests to `/v1/chat/completions` route through the `default` profile context.

**FR-041**: The system SHALL reject requests to unknown profile paths with a structured 404-class error containing the requested name, the list of available profile names, and a human-readable message.
- Acceptance: The error body is JSON with fields `profile_requested`, `profiles_available`, and `message`. No upstream call occurs.

**FR-042**: The system SHALL build a per-request profile context at request entry, immutable for the lifetime of that request, containing the resolved profile name, the merged slot map, the merged cascade chain, the resolved upstream provider reference, the parameter overrides, the web-search interception flags, and the compiled web-search regex.
- Acceptance: Concurrent requests through different profiles each see only their own profile context. No mutation of one context affects another.

### 4.6 Slot-Level Profile Overlay

**FR-050**: The system SHALL produce a profile's effective slot map by overlaying the profile's slot values onto the `default` profile's slot values, such that a slot absent from the profile resolves to the `default` profile's value for that slot.
- Acceptance: A profile with only `web_search` set inherits the `default` profile's values for every other slot.

**FR-051**: The system SHALL apply parameter overrides (temperature, max_tokens, top_p, frequency_penalty, presence_penalty) by replacing those fields in the dispatched request when the profile defines them, while leaving the original request body unmodified for fields not overridden.
- Acceptance: A profile with `parameters.temperature: 0.2` produces an upstream request with `temperature: 0.2` regardless of the client's submitted value.

### 4.7 Web-Search Tool-Call Interception

**FR-060**: The system SHALL inspect each request after profile resolution and before upstream dispatch for web-search tool invocations matching the profile's `web_search_pattern` (or the system default pattern when none is configured).
- Acceptance: Recognition works for OpenAI-style tool definitions (`tools[].function.name`), OpenAI tool_choice forcing (`tool_choice.function.name`), and Anthropic-style tool entries (`tools[].name` or `tools[].type` equals `web_search_20250305`).

**FR-061**: When the inspection detects a qualifying web-search invocation, the profile defines a `web_search` slot value, and the profile's `web_search_intercept` is true, the system SHALL rewrite the request's model field to the profile's `web_search` slot value before invoking the cascade router.
- Acceptance: The swap event is recorded with original and new model values and is visible in real-time stream entries.

**FR-062**: The system SHALL constrain the swap to cases where the web-search tool is the only tool invokable in the turn or where `tool_choice` explicitly forces the web-search tool, to avoid corrupting multi-tool reasoning contexts.
- Acceptance: A request with both a web-search tool and other tools, without explicit forcing, dispatches under the original (non-swapped) model.

**FR-063**: The system SHALL allow per-profile opt-out via `web_search_intercept: false` and per-profile pattern customization via `web_search_pattern`.
- Acceptance: A profile with interception disabled never triggers the swap. A custom pattern matches only tool names matching that pattern.

### 4.8 Profile Templates and Initialization

**FR-070**: The system SHALL ship with built-in templates for known CLIs: `pi`, `opencode`, `hermes`, `claude-code`, `codex`, plus `local-ollama` and `local-llamacpp` for self-hosted models, and `openai-bare`, `anthropic-bare` for direct provider routing.
- Acceptance: Each template produces a syntactically valid profile entry with sensible slot defaults and provider mappings.

**FR-071**: The system SHALL allow creating a new profile from a template via any configurator, with the operator filling in overrides interactively (TUI/WebUI) or via command flags (CLI).
- Acceptance: A profile created from a template is functionally identical regardless of which configurator was used.

**FR-072**: The system SHALL synthesize a starter `profiles.json` containing only the `default` profile (populated from the global configuration) the first time the proxy starts in a directory without an existing registry, so that operators have a working starting point with zero manual setup.
- Acceptance: A fresh install produces a working proxy on first launch without any user file authoring.

### 4.9 CLI Configuration Interface

**FR-080**: The system SHALL provide a command-line interface that runs as a single binary with subcommands for every configuration and operational task.
- Acceptance: Operators can perform every action the TUI and WebUI offer through CLI subcommands, including profile creation, editing, deletion, validation, provider management, log inspection, and analytics queries.

**FR-081**: The CLI SHALL provide the following top-level subcommands at minimum: `serve` (start the proxy), `tui` (launch the TUI), `web` (open the web dashboard in the browser), `profile` (profile management), `provider` (upstream provider management), `stats` (analytics queries), `logs` (request log inspection), `version`, `help`.
- Acceptance: Each subcommand documents its arguments via `--help` and produces structured exit codes (0 success, non-zero error).

**FR-082**: The CLI SHALL output structured data in JSON when `--json` is passed, suitable for piping to `jq` or other tools, and in human-friendly tables otherwise.
- Acceptance: Every read-style subcommand supports both output modes.

**FR-083**: The CLI SHALL validate every write operation (profile create, profile edit, provider add, etc.) before persisting and SHALL refuse to write invalid configurations, returning a non-zero exit code and a descriptive error.
- Acceptance: An attempt to create a profile with an unknown slot name fails before the registry is touched.

### 4.10 TUI Configuration Interface

**FR-090**: The system SHALL provide an interactive terminal user interface launchable via `proxy tui`, navigable entirely by keyboard, with multi-pane layouts and real-time updates.
- Acceptance: The TUI runs on any terminal supporting standard ANSI control sequences and remains responsive while the proxy serves traffic.

**FR-091**: The TUI SHALL present a main dashboard view showing (a) current request rate per profile, (b) circuit-breaker state per known model, (c) recent error rate, (d) a scrolling stream of the last N completed requests with profile, model, latency, status.
- Acceptance: The dashboard updates within one second of every served request.

**FR-092**: The TUI SHALL provide a Profile Manager view that lists profiles, displays the resolved overlay for a selected profile, and supports create, edit, duplicate, delete operations through keyboard-driven forms.
- Acceptance: Every operation honors the same validation as the CLI and writes to the same registry file.

**FR-093**: The TUI SHALL provide a Provider Manager view that lists configured upstream providers, supports adding new providers, editing tokens and base URLs, and shows provider health.
- Acceptance: Token edits are masked on screen, persisted to the configuration store, and applied without restart.

**FR-094**: The TUI SHALL provide an Analytics view with the same data the WebUI presents, rendered as ASCII/Unicode charts (sparklines, bar charts, distribution histograms) sized appropriately to the terminal viewport.
- Acceptance: The Analytics view supports the same time-window filters and grouping options as the WebUI.

**FR-095**: The TUI SHALL provide a Logs view that streams completed-request records in real time with filter chips for profile, model, status, and free-text search.
- Acceptance: Filters apply without lag; entering a search expression highlights matching records within 200 milliseconds.

**FR-096**: The TUI SHALL provide a Help view accessible from any context via `?` showing keyboard shortcuts relevant to the current view.
- Acceptance: Every interactive view documents its shortcuts.

### 4.11 Web Configuration Interface

**FR-100**: The system SHALL serve a web dashboard from the proxy process at a configurable port (default 8083), accessible via standard browsers, requiring no separate hosting.
- Acceptance: Visiting the configured URL after `proxy serve` returns a working dashboard.

**FR-101**: The web dashboard SHALL present a top-level Overview page showing the real-time request stream (FR-110), current key metrics (request rate, error rate, P95 latency, current cost per hour by profile), and a circuit-breaker health board.
- Acceptance: The Overview page renders within 500 milliseconds of navigation and updates without page reload.

**FR-102**: The web dashboard SHALL provide a Profile Manager page with list, detail, edit, create-from-template, duplicate, delete operations, all with live validation and an inline JSON preview of the persisted record.
- Acceptance: Every operation produces the same registry state as the equivalent CLI or TUI operation.

**FR-103**: The web dashboard SHALL provide a Provider Manager page mirroring the TUI Provider Manager (FR-093).
- Acceptance: Provider edits propagate to the running proxy without restart.

**FR-104**: The web dashboard SHALL provide an Analytics page (see FR-110 series).
- Acceptance: Per the Analytics requirements below.

**FR-105**: The web dashboard SHALL provide a Logs / Request Explorer page supporting search by profile, model, status code, time window, free-text content, and tool-call name; with detail views showing the full request body, response body, dispatched model, profile context, cost, latency, and any swap or fallback events.
- Acceptance: A query returning thousands of records paginates smoothly with virtualized scrolling.

**FR-106**: The web dashboard SHALL provide a Settings page for proxy-level configuration (port, auth key, default provider preference order, log retention policy, circuit-breaker thresholds), with live validation.
- Acceptance: Settings changes either apply immediately or clearly mark themselves as requiring restart with a banner.

### 4.12 Analytics and Reporting

**FR-110**: The system SHALL persist a request record for every completed request containing at minimum: request id, timestamp, profile name, slot resolved, model requested, model dispatched, upstream provider, prompt token count, completion token count, total token count, estimated cost in USD, latency in milliseconds, success/error class, error message (when applicable), tool call summary (count and names), swap event (when applicable), fallback event (when applicable).
- Acceptance: Every served request produces exactly one durable record visible in the Logs view.

**FR-111**: The system SHALL compute and display request volume over time, with grouping options by profile, model, slot, and provider, over selectable time windows from 1 hour to 90 days.
- Acceptance: The chart renders for any selected window in under 2 seconds at P95.

**FR-112**: The system SHALL compute and display latency distributions (P50, P95, P99, max) over time with the same grouping and window options as FR-111.
- Acceptance: Distribution charts are accurate against direct SQL queries on the request store.

**FR-113**: The system SHALL compute and display cost rollups in USD by profile, by model, by provider, by slot, and totals, over selectable windows, with cost-per-token rates sourced from a maintained pricing table that supports manual override per model.
- Acceptance: Cost calculations match independent spreadsheet computation against the same record set within rounding tolerance.

**FR-114**: The system SHALL compute and display error rate over time, broken down by error class (transient, auth, validation, internal, upstream-5xx, rate-limit, timeout).
- Acceptance: An induced error class produces the matching trend response in the chart within one minute of induction.

**FR-115**: The system SHALL compute and display token consumption over time, stacked by slot or by profile, with separate input/output breakdowns.
- Acceptance: Token totals reconcile with provider-reported usage within 2% tolerance, accounting for tokenizer differences.

**FR-116**: The system SHALL provide an Efficiency view plotting latency against tokens per request, with model and profile color coding, to identify outliers and cost-vs-speed trade-offs.
- Acceptance: The scatter plot supports brushing to filter the underlying record table.

**FR-117**: The system SHALL support exporting analytics views as CSV or JSON downloads and SHALL support generating PDF or HTML reports for a specified window (a "daily report" or "weekly report" form factor).
- Acceptance: A report download contains all charts as rendered images plus the raw data tables.

**FR-118**: The system SHALL retain request records for a configurable retention window (default 90 days), rolling older records to an aggregated form that preserves daily totals and distributions but discards per-request detail.
- Acceptance: Records older than the retention window appear in long-range analytics charts but not in the Logs detail view.

### 4.13 Real-Time Dashboard

**FR-120**: The system SHALL push request-completion events to connected web clients within one second of upstream completion, via WebSocket or Server-Sent Events.
- Acceptance: The Overview page's stream pane shows new entries with sub-second perceptible delay.

**FR-121**: The system SHALL push circuit-breaker state changes, provider health changes, and configuration changes to connected web clients as they occur.
- Acceptance: An induced circuit-breaker open event surfaces in the health board within one second.

**FR-122**: The system SHALL push aggregated metric updates (current rates, current costs, current error percentages) at a configurable interval (default once per second) so that dashboards remain accurate without per-event computation.
- Acceptance: Metric tiles smoothly update without flicker.

**FR-123**: The system SHALL support multiple concurrent dashboard connections without degraded real-time delivery to any individual connection.
- Acceptance: Ten concurrent dashboards see the same events with comparable latency.

### 4.14 Authentication and Authorization

**FR-130**: The system SHALL gate all proxy endpoints behind a shared-secret authentication key configurable via environment variable, config file, or configurator UI.
- Acceptance: Requests without the correct key receive a 401-class response; requests with the key pass through.

**FR-131**: The system SHALL bind to localhost by default and SHALL warn loudly (logs and dashboard banner) when configured to bind on any non-loopback address, given the proxy's role as a credentials-holder.
- Acceptance: Non-loopback binding requires an explicit `--allow-public` flag to suppress the warning, never silently.

**FR-132**: The system SHALL store upstream provider tokens encrypted at rest using a machine-bound encryption key (OS keychain integration where available, file-based key with restricted permissions otherwise).
- Acceptance: Tokens are not readable in plaintext via inspection of the configuration files; rotation works without service restart.

### 4.15 Observability

**FR-140**: The system SHALL emit a structured log record for every served request, every cascade fallback, every circuit-breaker transition, every configuration reload, and every authentication failure.
- Acceptance: Log records are JSON, machine-parseable, and contain enough context to reconstruct any incident.

**FR-141**: The system SHALL expose a `/healthz` endpoint returning the proxy's readiness state (registry loaded, providers reachable, persistence writable).
- Acceptance: The endpoint returns within 100 milliseconds and accurately reflects subsystem health.

**FR-142**: The system SHALL expose a `/metrics` endpoint in Prometheus exposition format for users who want to ingest metrics into external observability stacks.
- Acceptance: Standard Prometheus scrapers parse the output without errors.

### 4.16 OpenAPI and Discoverability

**FR-150**: The system SHALL serve a current OpenAPI 3.1 specification at `/openapi.json` reflecting all available endpoints including every defined profile's path-prefixed routes.
- Acceptance: Loading the spec into Swagger UI or Redoc renders a complete reference of the running proxy's surface.

**FR-151**: The system SHALL update the OpenAPI specification automatically when profiles are added or removed, without restart.
- Acceptance: Adding a profile produces a new path in the spec within one second; removing a profile removes it.

## 5. Non-Functional Requirements

### 5.1 Performance

**NFR-001**: Profile resolution and routing SHALL add no more than 2 milliseconds to request latency at P99 (excluding upstream time).
- Verified by benchmarks comparing the proxy in pass-through mode (no profile lookups) and full profile-routing mode against mock upstream.

**NFR-002**: Format translation (OpenAI <-> Anthropic) SHALL add no more than 5 milliseconds at P99 for non-streaming requests.
- Verified by translation benchmark over 10,000 representative request samples.

**NFR-003**: The proxy SHALL sustain at least 200 requests per second on a single core under typical request shapes.
- Verified by load test simulating typical mixed-profile traffic for 5 minutes.

**NFR-004**: Real-time event delivery SHALL achieve sub-second end-to-end latency from upstream completion to dashboard visualization at P95.
- Verified by instrumented measurement over 1000 events.

### 5.2 Reliability

**NFR-010**: The proxy SHALL recover automatically from upstream provider outages by retrying within cascade and reopening circuits according to the breaker policy without manual intervention.
- Verified by chaos test simulating provider unavailability for 5 minutes.

**NFR-011**: Configuration changes (profile edits, provider edits) SHALL never crash the proxy or interrupt in-flight requests.
- Verified by parallel test that performs config writes while sustaining load.

**NFR-012**: The proxy SHALL preserve durable state (request records, profile registry, provider configuration) across restarts without loss.
- Verified by restart test that checks all state survives a kill-and-restart cycle.

### 5.3 Security

**NFR-020**: Upstream provider tokens SHALL be encrypted at rest and never logged in plaintext.
- Verified by inspection of logs and persistent files after a session that exercises token-touching paths.

**NFR-021**: The proxy SHALL refuse to start with no `PROXY_AUTH_KEY` set unless `--allow-noauth` is passed explicitly.
- Verified by startup tests with and without the key.

**NFR-022**: All proxy endpoints SHALL respond with appropriate CORS headers when called from the bundled web dashboard origin and SHALL reject cross-origin requests from other origins.
- Verified by CORS preflight tests.

### 5.4 Usability

**NFR-030**: Every configurator (CLI, TUI, WebUI) SHALL expose every configuration capability; no capability is configurator-exclusive.
- Verified by test matrix mapping every config operation to all three interfaces.

**NFR-031**: The TUI SHALL be usable on terminals down to 80x24 by adapting layout to viewport size, with critical features remaining accessible.
- Verified by visual regression test at standard terminal sizes.

**NFR-032**: The WebUI SHALL be usable on viewports from 1024px wide upward and SHALL gracefully degrade analytics features on smaller mobile viewports.
- Verified by responsive layout tests.

**NFR-033**: First-launch experience SHALL produce a working proxy with no user file authoring required; the operator sees a "ready to serve" message within 10 seconds of issuing `proxy serve`.
- Verified by clean-machine install test.

### 5.5 Maintainability

**NFR-040**: All persistent data SHALL be stored in plain-text formats (JSON for configuration, SQLite for analytics) editable with standard tools without requiring the configurator.
- Verified by file format inspection.

**NFR-041**: Adding a new upstream provider type SHALL require code changes in a single dedicated module, not scattered changes across the codebase.
- Verified by structural code review.

## 6. Key Entities

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| Profile | A named bundle of routing and parameter overrides | Name, slot map, cascade map, provider_override, parameters, web-search settings, notes | Belongs to Registry; consumed by Profile Context |
| Profile Registry | The persistent set of all profiles | File path, last-loaded mtime, parsed content | Contains Profiles |
| Profile Context | A per-request frozen object carrying resolved profile state | Name, merged slot map, merged cascade, resolved provider, parameters, web-search regex | Created at request entry; consumed by router and interceptor; discarded after response |
| Upstream Provider | An LLM service reachable by the proxy | Name, base URL, wire format kind, encrypted token, health state | Referenced by profiles and global preference order; targeted by Dispatched Requests |
| Slot | A named role in the model router | Slot name, default model identifier | Referenced by Profile slot maps and by the global router |
| Cascade Chain | An ordered model list for fallback resolution | Slot name, ordered model list | Belongs to a Profile or to the global config |
| Circuit Breaker State | The per-model availability indicator | Model id, state (closed/open/half-open), failure samples, opened-at timestamp, cooldown end | Consulted by the dispatcher |
| Request Record | The durable log of one served request | Request id, timestamp, profile, slot, model_requested, model_dispatched, provider, token counts, cost, latency, status, error, tool summary, swap event, fallback event | Belongs to the analytics store; queryable by all analytics views |
| Web-Search Match Pattern | Regex for identifying web-search tool calls | Pattern string, scope (per-profile or default) | Belongs to a Profile or to the system default |
| Pricing Table | Maintained per-token cost rates for each known model | Model id, input cost per token, output cost per token, last-updated timestamp | Used by cost computation; manually overridable per model |

## 7. Success Criteria

SC-001: An operator can run pi, opencode, hermes, claude-code, and codex concurrently against a single proxy instance, each with independent slot bundles, with no restarts and no environment-variable contention.

SC-002: Web-search tool invocations from a profile defining a `web_search` slot dispatch to that slot's model in 100% of qualifying turns.

SC-003: An operator can perform every configuration operation (create profile, edit profile, manage providers, adjust settings) using whichever of the three configurators (CLI, TUI, WebUI) is most convenient at the moment, with identical resulting state.

SC-004: The web dashboard's real-time stream reflects every served request within one second of upstream completion at P95.

SC-005: Historical analytics queries over a 30-day window of 100,000 records return within 2 seconds at P95.

SC-006: A fresh install with no prior configuration files produces a working proxy ready to serve traffic within 10 seconds of issuing `proxy serve`, including seeded built-in profiles.

SC-007: Configuration changes (profile edit, provider edit) take effect on the next request without proxy restart in 100% of cases.

SC-008: The proxy sustains 200 requests per second on a single core in mixed-profile traffic without exceeding P99 latency overhead of 2 milliseconds for profile resolution.

## 8. Prior Art Analysis

### 8.1 Existing Solutions

| Solution | Strengths | Weaknesses | Gap This Project Fills |
|----------|-----------|------------|----------------------|
| LiteLLM Proxy | Comprehensive cost tracking, virtual keys, model_group_alias, mature analytics dashboard with model activity and budget controls | Cannot inspect tool-call payloads to rewrite the model field mid-request; designed for upstream gateway role rather than per-CLI tool-role overlay; heavyweight to deploy for personal use | Lightweight personal-scale alternative with tool-call interception and per-CLI profile isolation |
| claude-code-router | Task-category routing, dynamic `/model` switching, broad provider support, real-time logs | Single global config per running instance; no per-client profile isolation; no TUI; no rich analytics | Multi-CLI concurrent isolation, three-way configurator surface, integrated analytics |
| CCS (kaitranntt/ccs) | Multi-runtime bridging (Claude Code, Codex, Droid), OAuth account switching, visual dashboard with usage tracking and live auth monitor | Profile semantics centered on account/runtime rather than slot-level overlay; coarser routing granularity | Slot-granular per-CLI overlay model with tool-call interception |
| OpenCode (anomalyco) Ink-based TUI rewrite | Production-quality TUI patterns using Ink 6.6 + React 19; modern keyboard-driven multi-panel UX | A coding assistant, not a proxy; routing surface is upstream of OpenCode's concerns | Adopts Ink TUI patterns for proxy configurator and operational dashboard |
| Multiple instances per CLI | Trivial isolation, no code changes | 5x memory cost, 5x compression-layer cost, configuration sprawl, defeats unified analytics | Single-instance architecture preserving unified observability |

### 8.2 Patterns Adopted

The path-based profile selection follows CCS's convergent profile-selector pattern. The slot vocabulary (`default`, `background`, `think`, `long_context`, `image`, `web_search`) is adopted from the established conventions of claude-code-router and similar proxies so that profile entries map directly to roles operators already understand. The TUI architecture is adopted from the Ink + React 19 pattern proven by OpenCode's TUI rewrite. The WebUI analytics structure (Model Activity, cost dashboards, latency distributions, efficiency scatter) is adopted from LiteLLM's dashboard patterns, generalized to per-profile rather than per-team granularity. Real-time event delivery via WebSocket-style push is adopted from established observability product conventions (Grafana live, Sentry real-time).

### 8.3 Patterns Avoided

Filesystem-watcher hot-reload, profile inheritance via explicit `_inherits` chains, header-based profile selection, model-name-prefix profile encoding, triple-hop resolution combining multiple selection mechanisms, default-profile synthesis when the registry exists but omits the `default` key, environment-variable interpolation in profile values: each was evaluated and rejected, with rationale documented in `future-plans.md`. The common thread is that each adds maintenance surface, debugging difficulty, or selection ambiguity without solving a problem the chosen primitives leave unsolved.

## 9. Assumptions and Dependencies

### Assumptions
- The operator runs the proxy on a workstation or homelab machine they control; multi-user authorization is out of scope.
- Upstream provider APIs remain reasonably stable in their wire formats (OpenAI Chat Completions, Anthropic Messages, Ollama OpenAI-compatible).
- The operator has at least one upstream provider with valid credentials before issuing real requests; the proxy supports adding more later.
- Network connectivity to upstream providers is the operator's responsibility; the proxy reports unreachability rather than masking it.

### Dependencies
- Bun runtime version 1.2 or later for execution.
- A modern terminal supporting ANSI control sequences for TUI features (any of: iTerm2, WezTerm, Alacritty, Kitty, GNOME Terminal, Windows Terminal).
- A modern browser supporting WebSocket and SSE for WebUI features (Chrome 120+, Firefox 120+, Safari 17+).
- SQLite 3.40 or later for analytics persistence (bundled with Bun).

## 10. Identified Risks

| # | Risk | Severity | Mitigation | Related Req |
|---|------|----------|-----------|-------------|
| 1 | Format translation between OpenAI and Anthropic loses tool-call fidelity | High | Comprehensive test corpus for round-trip translation; preserve unknown fields | FR-002 |
| 2 | Circuit breaker false-positives during transient provider weather | Medium | Conservative defaults (5 failures in 60s), half-open probe before close, manual reset via configurator | FR-022 |
| 3 | Analytics storage growth unbounded over long retention windows | Medium | Configurable retention with rollup to daily aggregates beyond detail window | FR-118 |
| 4 | Real-time push connection saturation under high request rate | Medium | Server-side coalescing of events at the configured push interval; backpressure handling per connection | FR-122, FR-123 |
| 5 | Three configurator surfaces drifting in capability or behavior | High | Shared backend service layer; integration test matrix that exercises identical operations across all three configurators | NFR-030 |
| 6 | Profile context leaking across concurrent requests | High | Frozen per-request context, no module-level mutable caches except mtime-keyed registry | FR-042 |
| 7 | Token encryption-at-rest key management complexity | Medium | OS keychain integration where available, fallback to restricted-permission file key | NFR-020 |
| 8 | Bun runtime compatibility on Windows or older environments | Medium | Document supported platforms explicitly; provide WSL2 instructions for Windows operators | (deployment) |

## 11. Scope Boundaries

### In Scope

The complete proxy: request handling for OpenAI and Anthropic protocols including translation between them, streaming response support, upstream provider abstraction supporting multiple wire formats, cascade routing with circuit breaker, profile registry with overlay semantics, web-search tool-call interception, three-way configurator surface (CLI args, Ink-based TUI, Svelte-based WebUI), historical analytics with multiple chart types and grouping options, real-time event push to web clients, request record persistence with configurable retention, authentication via shared-secret key, encrypted token storage at rest, OpenAPI 3.1 spec generation that reflects defined profiles, Prometheus metrics export, healthz endpoint, profile templates for known CLIs and common deployment scenarios, structured logging for all significant events, CSV/JSON export of analytics views, PDF/HTML report generation, configurable retention policy with rollup.

### Out of Scope

Multi-user authentication and per-user authorization beyond the single shared-secret key. Hosted/SaaS deployment; the product is local-process-only. Mobile applications. Distributed deployment across multiple machines. Active load balancing across multiple proxy instances. Machine-learning-based routing decisions (the cascade and circuit breaker use deterministic rules). Caching of LLM responses for cost reduction (caching adds correctness risks that exceed the scope of this version). Prompt-injection detection. Content moderation or safety filtering. Custom plugin or extension API beyond the upstream provider abstraction.

### Future Considerations

The single deferred item that may be implemented when concrete pain emerges is multi-tool web-search dispatch (handling turns with web-search alongside other tools by split-dispatching the call). The rationale for keeping this deferred is documented in `future-plans.md`.

