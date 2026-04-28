# Final Report: Claude Code Middleware Gateway Pivot

> Updated: 2026-03-19

## Executive Decision

Recommended path:

- Use Claude Code Swap / CC Switch as the operator-facing switchboard.
- Pivot this repository into a focused Anthropic-compatible middleware gateway.
- Do not maintain course as a broad "ultimate proxy" platform.
- Do not fully replace the gateway with LiteLLM.
- Evaluate external focused gateways as benchmarks and possible partial upstream dependencies, not as blind replacements.

## Why This Decision Wins

### Maintain course as-is

Rejected.

Reason:

- The repository currently mixes gateway concerns with analytics, billing, alerts, dashboards, RBAC, GraphQL, and crosstalk.
- That scope is visible in [src/main.py](/home/cheta/code/claude-code-proxy/src/main.py#L4) through [src/main.py](/home/cheta/code/claude-code-proxy/src/main.py#L42) and [src/main.py](/home/cheta/code/claude-code-proxy/src/main.py#L271) through [src/main.py](/home/cheta/code/claude-code-proxy/src/main.py#L301).
- The most painful recent work is still Claude Code compatibility, tool continuation, and request/response transformation.

### Replace with external middleware

Rejected as the default path.

Reason:

- External projects are promising, but I did not find one with clearly documented coverage for the full recent Anthropic surface you care about:
  - adaptive thinking / effort
  - `output_config.format`
  - automatic caching
  - latest server tools
  - thinking signatures / fine-grained streaming deltas
  - late-2025 and early-2026 Claude Code runtime expectations

Use an external router only if you want to stop owning protocol fidelity and accept unknown compatibility gaps.

### Pivot this repo into the gateway layer

Accepted.

Reason:

- Your strongest differentiated asset is already the conversion layer and the repo-specific fixes around Claude Code behavior.
- You can keep that asset while shedding unrelated platform weight.

## Assessment Of External Projects

### 1. Claude Code Router / CCR

Strengths:

- Purpose-built for Claude Code routing and transformation.
- Strong ecosystem awareness and custom transformer model.

Risk:

- Public docs and README surface do not clearly prove full coverage of the latest Anthropic protocol additions you asked about.

Use:

- Benchmark and borrow ideas.
- Possible replacement only if you validate your exact feature matrix against it.

Codebase findings:

- Strong Anthropic-stream fidelity in `packages/core/src/transformer/anthropic.transformer.ts`, including:
  - `signature_delta`
  - `thinking_delta`
  - `input_json_delta`
  - `server_tool_use`
  - `web_search_tool_result`
- Count-token support is implemented at the server level with tokenizer-aware fallback in `packages/server/src/server.ts`.
- `cache_control` exists in the model layer but is often removed by provider-specific transformers such as `cleancache`, `openrouter`, `groq`, and `vercel`, which means caching compatibility is handled but not uniformly preserved.

Issue / PR history signals:

- PR #1275 fixes thought-signature edge cases.
- PR #1267 and #1266 fix thinking / reasoning compatibility problems.
- Issue #1252 reports `/v1/messages/count_tokens` problems.
- PR #1230 adds built-in web search support.
- PR #1220 specifically addresses cache breakage.

Source:

- https://github.com/musistudio/claude-code-router

### 2. Claude Code Mux

Strengths:

- Very aligned with the gateway problem.
- Public README/search snippet claims automatic failover, Anthropic-compatible streaming, and support for 15+ providers.

Risk:

- Strong marketing surface, but still needs field-by-field verification against your required Anthropic matrix.

Use:

- Best external benchmark for focused gateway scope.

Codebase findings:

- Strong focused routing in `src/router/mod.rs`, including:
  - web-search routing
  - think-mode routing
  - explicit subagent model extraction via `<CCM-SUBAGENT-MODEL>`
- `/v1/messages/count_tokens` is implemented and routed by provider in `src/server/mod.rs`.
- Anthropic-compatible providers are passed through directly in `src/providers/anthropic_compatible.rs`.
- OpenAI/Codex reasoning is transformed into Anthropic `thinking` blocks in `src/providers/openai.rs`.
- Significant gaps remain:
  - `tool_choice` is explicitly TODO in `src/providers/openai.rs`
  - no explicit `signature_delta` support was found
  - no explicit `server_tool_use` / `web_search_tool_result` output was found
  - `cache_control` exists in models but not as a clearly supported transform path

Issue / PR history signals:

- Issue #15 shows subagent-model matching bugs.
- Issue #9 reports streaming response corruption.
- Issue #7 reports missing identifying headers for Claude Code Max OAuth.
- Issue #6 requests per-model request parameter support.

Source:

- https://github.com/9j/claude-code-mux

### 3. kiyo-e/claude-code-proxy

Strengths:

- Clean, lightweight translation layer.
- Good reference for narrow proxy shape.

Risk:

- Smaller feature surface and less evidence of deep compatibility coverage.

Use:

- Design reference, not full replacement.

Source:

- https://github.com/kiyo-e/claude-code-proxy

### 4. LiteLLM

Strengths:

- Excellent OpenAI-centric gateway.
- Strong routing, fallbacks, budgets, and observability.

Risk:

- Its contract is fundamentally OpenAI input/output normalization, not Claude Code-first Anthropic fidelity.

Decision:

- Not the right center of gravity for this middleware project.

Source:

- https://docs.litellm.ai/

### 5. OpenRouter direct

Strengths:

- Best no-proxy option when you can stay within Anthropic-compatible usage and Anthropic models.

Risk:

- OpenRouter explicitly says Claude Code is optimized for Anthropic models and may not work correctly with other providers.

Decision:

- Great bypass path for some profiles, not a general replacement for middleware.

Source:

- https://openrouter.ai/docs/guides/coding-agents/claude-code-integration

## Authoritative Corrections To The Original Research Draft

Correct:

- Claude Code model configuration priority and `modelOverrides` behavior.
- Claude Code does not itself convert Anthropic Messages to OpenAI Chat Completions for arbitrary backends.

Correction:

- "OpenRouter Anthropic Skin behaves exactly like Anthropic API" is too strong.
- The current official OpenRouter guide says Claude Code is only guaranteed to work with the Anthropic first-party provider and may not work correctly with other providers.

## Required Project Split

### Keep in middleware core

- Anthropic request / response models
- request transformation
- response transformation
- streaming translation
- provider adapter contracts
- capability registry
- compatibility fixtures
- minimal health and logs

### Move to optional addon or separate repo

- web dashboard
- analytics / billing / reports
- alerts / notifications / predictive
- RBAC / user management
- GraphQL API
- crosstalk / experimentation

## Suggested Subprojects

### `cc-middleware-core`

Protocol compatibility and provider transforms.

### `cc-middleware-observability`

Usage tracking, logs, and minimal troubleshooting UI.

### `cc-ops-console`

RBAC, dashboards, provider onboarding, alerts, reports, integrations.

### `cc-labs`

Crosstalk, benchmark tooling, routing experiments.

## Update Method For Future Anthropic Changes

The matrix should be updated whenever either of these change:

- Claude Platform release notes: https://platform.claude.com/docs/en/release-notes/overview
- Claude Code changelog: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

Update loop:

1. Scan new entries since the last reviewed date.
2. Extract any new:
   - fields
   - headers
   - stop reasons
   - tool types
   - streaming event types
   - model capability changes
3. Add registry entries.
4. Mark each item `implemented`, `partial`, `passthrough-only`, or `missing`.
5. Add fixture coverage.
6. Regenerate the matrix and review it before release.

## Final Recommendation

Pivot this repo to the middleware role.

Let Claude Code Swap / CC Switch own switching, local takeover, and user-facing profile management.

Let this repo own Anthropic protocol fidelity.

That split is the cleanest way to preserve what ye already built without dragging a whole AI control plane behind every protocol bug.

## Updated External-Replacement Conclusion

After direct code inspection, my confidence is higher that:

- CCR is the stronger reference implementation for Anthropic-stream and server-tool fidelity.
- Mux is the stronger reference for a lean, focused gateway shape and subagent-aware routing.
- Neither repo, from public code alone, demonstrates complete coverage of all recent Anthropic protocol additions that matter to this project.

That strengthens the original recommendation:

- do not blindly replace this repository with either project,
- but do absorb their best ideas into the middleware refactor and matrix.
