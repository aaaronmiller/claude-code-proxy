# Quickstart: Model-Scan Integration

End-to-end walkthrough once the feature is implemented. Commands are illustrative of the target
UX defined in `design.md`.

## 1. Produce a snapshot (model-scan)

```bash
# Run a scan and emit the shared snapshot
model-scan --emit-snapshot
# default output: ~/.config/model-scan/routing_snapshot.json
# or serve it: GET http://127.0.0.1:8124/routing-snapshot
```

## 2. Enable consumption (router)

In `config/proxy_chain.json`:

```json
"model_scan": { "enabled": true, "policy": "free",
                "snapshot_path": "~/.config/model-scan/routing_snapshot.json" }
```

## 3. Bring the chain up (one command, visible monitor)

```bash
ccp up               # router + clip (if OAuth providers) + headroom + local model
                     # spawns a terminal with tmux panes (headroom ratios, proxy, clip)
ccp up --background  # detached, no monitor window
```

## 4. Launch a tool with a policy

```bash
ccp claude                         # default preset
ccp claude --policy free           # best free models for every role
ccp codex  --policy budget=0.50    # best models at or below 0.50 per million
ccp hermes                         # standby lane, free-only, full 15-role bindings
ccp ante                           # low-RAM agent, compression-class free
```

## 5. Session-scoped config and concurrent sessions

```bash
# A session file (preset + policy + per-role overrides)
cat > sessionA.yaml <<'EOF'
preset: claude
policy: rotate
roles:
  big:      { passthrough: true }
  toolcall: { model: qwen/qwen3-next-80b-a3b-thinking, provider: openrouter }
EOF

ccp claude --config sessionA.yaml   # ephemeral profile, e.g. /p/claude-7f3a/v1
ccp claude --config sessionB.yaml   # a second, independent session, same tool
```

## 6. Verify bindings and rotation

```bash
curl -s -X POST http://127.0.0.1:8082/api/proxy/reload-models | jq .
                                               # shows bound model + source per tier/role
ccp errors --provider anthropic              # filter the unified error log
ccp errors --session claude-7f3a             # trace one session's activity
```

## 7. Expected results

- Every bound role shows a model and a non-empty cascade; provenance marks snapshot vs static.
- Killing the primary provider recovers via the cascade with no manual edit.
- Interactive primary stays S-tier within quota, falls to the free floor (deepseek-v4-flash or a
  better free S-tier) when paid quota is spent; standby agents stay on free.
- With the snapshot removed, tools still launch on static config.
