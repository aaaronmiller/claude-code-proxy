---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, compression, caching, headroom, rtk, hermes-lcm, prompt-cache]
---

# F08: Compression and Caching Layer

> STATUS v1.1: BUILT (mostly). Headroom always-on base :8787 (15 settings), semantic cache +
> token cache present. TO DO: surface RTK tokens-saved stats; expose cache-state signal for
> cache-aware decisions; context engine (hermes-lcm) optional. "(PROPOSED)" tags below superseded
> by 01-CURRENT-STATE.

Scope: integrate the third-party compression tools and handle provider prompt caching
correctly. Note on naming: the user's "retk" is RTK in the docs. "Kompressor" is the model-level
compression mechanism Headroom uses (operates on model weights via quantization/sparsification,
orthogonal to context compression, no cache downside). (`Optimal compression for hermes
agent.md:78-82`)

## Tools and request-path ordering

- RTK: shell/terminal-output compression via CLI hooks; transport layer, runs first.
  (`Optimal compression for hermes agent.md:84-88`) (CURRENT)
- Headroom: input/prompt compression 70-90%, at /home/cheta/code/input-compression/, port 8787
  (authoritative; 8001 is a superseded draft). (`:78-83,250-261`; `unified_project_idea_record.md:94-101`) (CURRENT)
- Context engine on assembled context: hermes-lcm (primary) OR pi-context-prune (alt) OR built-in
  (skip). (`Optimal compression...md:52-77`)
- Order: RTK (transport) -> Headroom (input) -> context engine. RTK and Headroom compress before
  tokens hit context, so they are cache-transparent and stay always-on. (`:239-247,265-296`)

## hermes-lcm (context engine)

- DAG + SQLite + source lineage; lossless originals; 7 recovery tools (lcm_grep/expand/
  expand_query/describe/load_session/status/doctor). (`:52-62,180-208`)
- Tuning: LCM_CONTEXT_THRESHOLD=0.35, FRESH_TAIL=64, LEAF_CHUNK=20000, dynamic leaf chunk on,
  externalize payloads >12000 chars. (`:284-296`)

## Caching strategy

- Write-time selection beats post-hoc eviction; reprocess cost scales linearly with context, so a
  lower threshold (0.35) reduces bust cost. (`:14-21,130-138,210-228`)
- Cache-aware pre-tokenization, header/footer detection, semantic + exact-match cache. (`Proxy
  update plan.md:42-43,2419-2423`)

## Hard requirements

- Do NOT stack pi-context-prune on hermes-lcm; it destroys lossless lineage. Use one. (`Optimal
  compression...md:233-247`)
- RTK + Headroom always on, zero cache downside. (`:265-296`)
- Cross-model prompt caches are NOT shared: each model pays its own prefill. Routing (F04) must
  not assume a warm cache across model switches. (`:159`)
- hermes-lcm has no provider/model TTL heuristics or cache-break tracking; the gateway is the
  natural place to expose cache-state signals. (`:182-190`)
- Kompressor (Headroom's model-weight compression) and RTK/Headroom are orthogonal to context
  compression and have no cache downside; keep them on. (`:78-88`)

## Dependencies

- RTK/Headroom/CLIProxyAPI are stages in the chain (F02); compression stats surface in the status
  bars (F16) and observability (F11). RTK stats are currently missing from the terminal display
  and must be added. (`unified_project_idea_record.md:102-106,433-439`)

## Open questions

- hermes-lcm Embed (in-process) vs Invoke (sidecar)?
- Where to expose the cache-state/cache-break signal hermes-lcm lacks (F01 vs F11)?
