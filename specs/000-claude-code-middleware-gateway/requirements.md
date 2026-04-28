# Claude Code Middleware Gateway Requirements

> Updated: 2026-03-19
> Scope: transform this repository into a focused Anthropic-compatible middleware gateway designed to sit behind Claude Code Swap / CC Switch and in front of alternative backend model providers.

## Goal

Turn this project into a high-fidelity Claude Code middleware layer whose primary responsibility is:

1. Accept Claude Code's Anthropic Messages API traffic.
2. Preserve Claude Code behavior and newer Anthropic protocol features.
3. Translate requests and responses for non-Anthropic providers.
4. Expose a maintained compatibility matrix and update workflow as Anthropic changes the protocol.

## Why

The current repository has drifted into a broader platform with dashboards, analytics, RBAC, alerts, billing, reports, GraphQL, and crosstalk, while the most operationally sensitive surface is still protocol translation and Claude Code compatibility.

The middleware role should be narrowed and strengthened, not buried under unrelated product scope.

## Target Deployment Model

- Claude Code and Agent SDK clients continue to point at an Anthropic-compatible endpoint.
- Claude Code Swap / CC Switch is used as the outer profile manager / local proxy / app switcher.
- This project becomes the protocol gateway behind that switcher for profiles that need Anthropic-to-non-Anthropic translation.
- For true Anthropic-compatible backends, the gateway may operate in passthrough mode.

## Functional Requirements

### FR-1: Anthropic Messages API Fidelity

The gateway must provide first-class support for:

- `POST /v1/messages`
- `POST /v1/messages/count_tokens`
- Anthropic-compatible streaming responses
- Anthropic request / response headers required by Claude Code and the Agent SDK

Success criteria:

- Claude Code can use the gateway without custom client patches.
- Claude Agent SDK requests using Claude Code as runtime remain compatible.

### FR-2: Request Transformation Fidelity

The gateway must accurately transform Anthropic request semantics to upstream provider semantics for:

- top-level `system`
- `messages`
- multimodal content blocks
- `tools`
- `tool_choice`
- `thinking`
- `effort`
- `stop_sequences`
- structured outputs via `output_config.format`
- release-note-driven request parameters such as `cache_control`, `inference_geo`, `speed`, and future additions

Success criteria:

- Every supported Anthropic request field is classified as `passthrough`, `transform`, or `unsupported-with-explicit-error`.

### FR-3: Response Transformation Fidelity

The gateway must accurately transform upstream provider responses back into Anthropic Messages API semantics for:

- text content
- `tool_use`
- `tool_result`
- `thinking`
- `redacted_thinking`
- structured outputs
- stop reasons
- usage accounting

Success criteria:

- No silent field dropping for supported features.
- Unsupported upstream behaviors are surfaced explicitly in logs and capability metadata.

### FR-4: Streaming Event Fidelity

The gateway must support Anthropic SSE event semantics, including:

- `message_start`
- `content_block_start`
- `content_block_delta`
- `content_block_stop`
- `message_delta`
- `message_stop`
- fine-grained tool streaming with `input_json_delta`
- thinking signatures and future streaming delta variants

Success criteria:

- Claude Code tool use, thinking blocks, and resume behavior remain intact under streaming.

### FR-5: Tooling Compatibility Matrix

The gateway must maintain an authoritative transformation matrix covering:

- client tools
- server tools
- built-in Claude tool surfaces introduced after mid-2025
- programmatic tool calling
- skills / container-coupled tool surfaces where relevant

Success criteria:

- Each tool surface is mapped to current gateway handling status:
  - implemented
  - partial
  - passthrough-only
  - unsupported

### FR-6: Claude Code Feature Coverage Tracking

The gateway must explicitly track compatibility with Claude Code and Anthropic platform features added in late 2025 through early 2026, including:

- adaptive thinking / effort
- fine-grained tool streaming
- structured outputs GA migration to `output_config.format`
- tool search
- programmatic tool calling
- memory tool
- web search / web fetch
- code execution / skills-related protocol surfaces where applicable
- automatic caching
- current stop reasons
- subagent-specific model routing

Success criteria:

- Feature coverage status is documented and tied to code paths or explicit gaps.

### FR-7: Capabilities Registry

The gateway must introduce a machine-readable capabilities registry that records:

- Anthropic surface area
- per-provider support
- required transforms
- known caveats
- test fixture coverage

Success criteria:

- The registry becomes the source of truth for generated docs and compatibility checks.

### FR-8: Release-Driven Update Workflow

The gateway must define a repeatable way to detect and process new Anthropic protocol changes from:

- Claude Platform release notes
- Claude Code changelog
- Anthropic model / capability docs

Success criteria:

- A maintainer can update the registry and matrix in a single documented workflow after an Anthropic release.

### FR-9: Compatibility Test Harness

The gateway must define automated compatibility fixtures for:

- request transformation
- response transformation
- SSE event fidelity
- tool schema normalization
- stop reason mapping
- token counting behavior
- provider adapter behavior

Success criteria:

- New Anthropic features cannot be marked supported without fixture coverage or an explicit exception entry.

### FR-10: Claude Code Swap / CC Switch Integration

The gateway must document and support its role when paired with Claude Code Swap / CC Switch:

- what CC Switch owns
- what the middleware owns
- how profiles should be wired
- when to bypass the middleware

Success criteria:

- Operators can decide per-profile whether traffic should go:
  - Claude Code -> CC Switch -> Middleware -> provider
  - Claude Code -> CC Switch -> provider directly

### FR-11: Focused Scope

The middleware project must define non-goals and move non-core features out of the gateway core.

Non-goals for the middleware core:

- billing product
- dashboard platform
- alerting platform
- GraphQL API
- crosstalk / debate product
- multi-user RBAC product
- reporting product

Success criteria:

- Existing features are classified as:
  - core middleware
  - optional addon
  - separate subproject
  - archive

## Quality Requirements

### QR-1: Explicitness Over Best-Effort Guessing

If a feature is unsupported, the gateway must emit an explicit compatibility error or degrade via a documented fallback path. Silent dropping is not acceptable.

### QR-2: Source-Linked Documentation

Every transformation rule in the matrix must cite:

- relevant Anthropic docs or changelog entry
- gateway implementation file
- support status

### QR-3: Backward-Compatible Adapters

Provider-specific adapters must not be hardcoded into the core protocol model. They must be capability-driven where practical.

### QR-4: Upstream Truth For Token Counting

`/v1/messages/count_tokens` should eventually use upstream-accurate counting or an Anthropic-compatible capability contract, not a rough character heuristic.

## Existing Repository Components To Reclassify

Core candidates:

- `src/services/conversion/*`
- Anthropic-facing endpoints
- provider routing / adapters
- essential logging and compatibility tests

Likely addon or subproject candidates:

- analytics / billing / reports
- alerts / notifications / predictive
- dashboards / websocket live UI
- RBAC / users / GraphQL
- crosstalk

## Deliverables Required By This Spec

- `requirements.md`
- `design.md`
- `transformation-matrix.md`
- `final-report.md`
