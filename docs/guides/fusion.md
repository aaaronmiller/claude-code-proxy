# OpenRouter Fusion

OpenRouter Fusion runs a panel of models in parallel, then a judge compares their
answers and returns structured analysis for the final model response.

This proxy exposes Fusion two ways:

1. Proxy alias: set a client model to `fusion`, `fusion/<profile>`, `ccp/fusion`, or `openrouter/fusion`.
2. One-shot CLI: run `ccp-fusion <profile> <prompt>` from any agent or shell.

## Recommended Setup

Use the CLI for arbitrary one-off prompts from Codex, Hermes, Pi Agent, Qwen, or
Claude Code:

```bash
ccp-fusion free "Compare these two approaches and call out failure modes"
```

Pipe stdin for longer prompts:

```bash
cat prompt.md | ccp-fusion free
```

Use the proxy alias when an agent session should route a tier through Fusion:

```bash
MIDDLE_MODEL=fusion
FUSION_PROFILE=free
FUSION_FREE_ANALYSIS_MODELS=openrouter/free,openrouter/free,openrouter/free
FUSION_FREE_MODEL=openrouter/free
```

With Claude-style routing, `MIDDLE_MODEL=fusion` means Sonnet-class requests map
to `openrouter/fusion`. With OpenAI-format clients, request `model: "fusion"` or
`model: "fusion/research"` to select a named Fusion profile for that request.

## Environment

`FUSION_PROFILE`
: Default profile name. Defaults to `free`.

`FUSION_ALIASES`
: Extra comma-separated aliases that should trigger Fusion.

`FUSION_<PROFILE>_ANALYSIS_MODELS`
: Comma-separated panel models. Defaults to three `openrouter/free` entries.

`FUSION_<PROFILE>_MODEL`
: Judge/final model. Defaults to `openrouter/free`.

`FUSION_<PROFILE>_PRESET`
: OpenRouter preset slug such as `general-budget`. Explicit models override the
preset.

`FUSION_<PROFILE>_FORCE`
: If true, the CLI and tool-only requests set `tool_choice=required`.

`FUSION_PROFILES`
: JSON profile map. This is useful for multiple named presets:

```json
{
  "free": {
    "analysis_models": ["openrouter/free", "openrouter/free", "openrouter/free"],
    "model": "openrouter/free",
    "force": true
  },
  "budget": {
    "preset": "general-budget",
    "force": true
  }
}
```

## CLI vs MCP

CLI is the default choice. It costs zero prompt tokens until invoked, works from
any agent that can run shell commands, and keeps Fusion profiles in env.

MCP is only worth adding if an agent needs tool discovery or structured tool
calling for Fusion. The tradeoff is token overhead: every MCP session advertises
the tool schema and instructions even when Fusion is not used.

## Notes

OpenRouter Fusion is provider-specific. The proxy sends Fusion requests to an
OpenRouter-compatible upstream (`https://openrouter.ai/api/v1` or the configured
Headroom OpenRouter relay).

In coding-agent sessions with many user tools, Fusion invocation is model-decided.
`tool_choice=required` can force Fusion only when there are no competing tools,
which is why the CLI is the reliable explicit path.
