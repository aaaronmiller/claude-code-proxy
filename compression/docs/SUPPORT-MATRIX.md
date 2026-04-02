# Support Matrix

This kit does not treat every CLI the same. The support level depends on whether the tool exposes hooks, supports custom API endpoints cleanly, and already contains its own context-compaction layer.

## Current Support

| CLI | RTK Hook | Headroom Routing | Install Mode | Notes |
|-----|----------|------------------|--------------|-------|
| `claude` | Full | Full | config patch + wrappers | Best-supported path. Hook patching is stable and Headroom MCP can also be installed. |
| `qwen` | Full | Mixed | config patch + wrappers | RTK hook is fine. Headroom works only through OpenAI-compatible auth mode, so compressed launcher is explicit and not silent. |
| `codex` | None | Wrapper | wrappers only | No hook integration added here. Use `codex-compressed` or `compressctl run codex`. |
| `opencode` | None | Wrapper | wrappers only | Launcher support only. No config mutation yet, and no native compaction claim is made here. |
| `openclaw` | None | Experimental wrapper | wrappers only | OpenClaw already has internal context pruning and compaction. External Headroom should be considered experimental. |

## Why The Split Exists

- RTK needs a pre-tool hook surface.
- Headroom proxying needs either provider env vars, CLI flags, or a clean config path.
- Some CLIs already mutate context internally, so layering more compression can help or can distort behavior.

## Runtime Strategy

The installer uses three tiers:

1. Full integration
   Claude and Qwen hook patching where the host config format is well-understood.

2. Wrapper integration
   Generated `*-compressed` and `*-direct` launchers handle proxy env routing without mutating the base CLI.

3. Experimental integration
   OpenClaw is left wrapper-only because its existing context compaction, routing, and provider model system are already more opinionated than the others.

4. Generic fallback
   Any CLI in `PATH` can be launched through `compressctl exec --mode compressed --command <name>` even before we define first-class support.

## Activation Model

The intended steady-state UX is global:

- `compressctl on`
  Plain CLI invocations are routed through managed shims and compression-aware config.

- `compressctl off`
  Plain CLI invocations bypass compression and managed hook entries are removed where supported.

The `*-compressed` and `*-direct` commands remain available as debugging and escape-hatch paths, not as the primary product UX.

## Practical Guidance

- Use `claude-compressed` when you want the full stack.
- Use `qwen-compressed` only when you intend to run Qwen in OpenAI-compatible auth mode.
- Use `codex-compressed` and `opencode-compressed` as low-risk routing wrappers.
- Treat `openclaw-compressed` as a test path, not the default production route.
- Treat `opencode-compressed` as a pure wrapper path until its config and transport semantics are audited more deeply.
- Use `compressctl wrap <alias> <command>` when you want durable named wrappers for an otherwise unsupported CLI.

## Future Work

- Add formal config-patching support for tools beyond Claude and Qwen only after their endpoint semantics are audited line by line.
- Add per-tool smoke tests that prove compressed and direct launchers preserve auth and model selection.
