---
date: 2026-06-17 00:00:00 PT
ver: 2.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, memory, wiki-memory, hooks, hooks-emulation, content-injection, mem]
---

# F09: Memory Integration and Hooks Emulation

The one genuinely-new core module (no proxy integration exists yet). Two halves: (a) wire the
user's bespoke memory system at `/home/cheta/code/wiki-memory` into the request path via
content-injection (recall, pre-request) and storage hooks (persist, post-response); (b) a
hooks-emulation bus so CLIs that lack native hooks gain the same behavior uniformly because the
gateway is the interception point. Hooks emulation IS the memory integration mechanism.

## A. What wiki-memory actually is (verified from repo)

- Hot tier = `memory/mem.py`: pure-stdlib Python store of short recallable facts in a local JSON
  file `$AI_WIKI/.meta/memory.json`, scored by keyword overlap + recency decay (30d) + pin boost.
  Best-effort mirror to ClawMem. THIS is the surface the gateway drives.
- Warm tier = `dream/dream_agent.py`: compiles transcripts into git-backed YAML+markdown wiki
  pages with frontmatter + `[[wikilinks]]`. Runs detached at session end; not on the hot path.
- Optional ClawMem REST service at `:7438` (SQLite + FTS5 + vec) for warm/cold search. Optional,
  often down; JSON file is the source of truth. ClawMem absence is non-fatal.
- MCP is only spec'd (port 7439, `wiki_search/wiki_query/wiki_ingest`) and DISABLED. No server
  code exists. Do NOT depend on MCP for memory; use in-process import or the CLI.

## B. Integration contract (the API to call)

Recommended: in-process `import mem` (cleanest, no network, no subprocess). CLI and the unified
hook dispatcher are fallbacks.

Store/write (`memory/mem.py`):
- `MemoryStore(path=MEMORY_DB)` (`mem.py:142`)
- `store.add(content, tags=None, project="default", source="unknown", pinned=False) -> dict|None`
  (`mem.py:184-209`); dedups per project, atomic JSON write, then best-effort ClawMem forward.
- `capture_from_transcript(path, source, project, store=None) -> list` (`mem.py:313-345`),
  marker-driven conservative capture.
- `_detect_save_directive(text) -> str|None` (`mem.py:407-419`), extracts "remember that X".
- Record shape: `{id:"mem-<hex16>", content, tags[], project, source, pinned, created, accessed,
  access_count}` (`mem.py:19-30`).

Recall/read (`memory/mem.py`):
- `store.recall(query, limit=8, project=None) -> list` (`mem.py:217-231`).
- `store.recent(limit=6, project=None) -> list` (`mem.py:252-255`) for query-less session-start.
- `store.all / forget / stats`.

Injection (`memory/mem.py`):
- `render_injection(memories, header) -> str` (`mem.py:393-402`) emits:
  `<memory source="wiki-memory" hint="HEADER">\n- 📌 content [tags]\n- content\n</memory>`.

CLI fallback: `mem.py save|recall|inject|capture|list|forget|stats`.
Hook dispatcher fallback: `hooks/memory_hook.py <session-start|user-prompt|session-end>` reads
hook JSON on stdin, always exits 0 (never breaks a session).

## C. Gateway wiring

Pre-request hook (inject):
- query = incoming user message; `recall(query, limit=MEMORY_INJECT_LIMIT, project=<id>)`;
  `render_injection(...)`; prepend the block to the request. Fall back to `recent()` if no usable
  query.
- Also run `_detect_save_directive(user_msg)`; on hit, `store.add(..., pinned=True)` and surface a
  `<memory-saved>` marker.

Post-response hook (store):
- Gateway decides what to persist. Either call `store.add(content, project=<id>,
  source="gateway")` for chosen facts, or append the turn to a transcript and
  `capture_from_transcript`. Marker-only auto-capture will NOT grab arbitrary response text, so
  explicit `add()` is required for gateway-curated memory.

Config the gateway must set (process has no meaningful cwd):
- `AI_WIKI`, `MEMORY_DB`, `MEMORY_PROJECT` (explicit, do not rely on cwd basename),
  `MEMORY_RECALL_LIMIT`/`MEMORY_INJECT_LIMIT`, `CLAWMEM_URL`/`CLAWMEM_ENABLED`, `MEMORY_SOURCE`.

## D. Hooks-emulation bus (the universal part)

The gateway exposes a hook lifecycle to EVERY routed CLI, including those with no native hooks:
- Events: session-start, pre-request (user-prompt), post-response, session-end. Plus tool
  pre/post if useful.
- Each event runs registered handlers; the memory handlers above are the first consumers. This
  generalizes Claude Code style hooks (ref TeammateIdle/TaskCompleted exit-code-2,
  `Claude Code Backend Middleware - Project Assessment.md:804-810`) to Pi, Qwen, Codex, etc.
- Output-form negotiation: emit plain stdout block (default), Claude structured
  `{"hookSpecificOutput":{...,"additionalContext":...}}` when `MEMORY_HOOK_STRUCTURED=1`, or
  Hermes `{"context": block}` (`cli/hermes-pre-llm.py:43`). Cleanest: gateway calls
  `render_injection()` in-process and injects the raw block itself, bypassing envelope guessing.

## E. Control MCP server (gateway's own, separate from wiki-memory)

Built-in MCP control surface (streamable HTTP, mandatory auth) so models self-manage routing:
switch_provider/model, set_role, get_routing_stats, open/close_circuit, set_budget_limit,
list/set_active_chain, pause_provider. (`PRD- MAUG.md:519-539`). This is the gateway control
plane, distinct from wiki-memory (which has no live MCP).

## Hard requirements

- Injected memory must not break prompt caching: inject as a stable prefix block, carry metadata,
  coordinate with F08 (cache-state). Token-cap the injection (cap `limit`; mem.py does not enforce
  char limits; honor a `memory_char_limit`).
- Writes need a file lock: the JSON store is full-file atomic-replace with no locking; concurrent
  gateway writes lose updates (last-writer-wins). Add a lock around `add()` for multi-session use.
- Treat the JSON file as source of truth; ClawMem optional and non-fatal.
- Control MCP auth mandatory; no unauthenticated routing mutation.
- Memory hooks must never break a request (mirror memory_hook.py always-exit-0 behavior).

## Dependencies

- Pre/post hooks wrap F01 request handling; injection precedes F04 routing; project id from the
  session context (F10). Coordinates caching with F08.

## Open questions

- Persistence policy: which post-response content does the gateway auto-store vs only explicit
  "remember"? Recommend: explicit directives always; otherwise opt-in per session/role.
- Per-session project scoping: one project per harness session, or per workspace?
- Embed warm-tier (ClawMem vector search) into recall, or keep hot-tier keyword recall only for v1?
