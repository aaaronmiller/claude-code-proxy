<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->

## Constitution

This project is governed by `.specify/memory/constitution.md` (v1.0.0). It defines SIX core
principles plus three engineering constraints and the development workflow. The names below are
the authoritative list; an earlier abbreviation in this file was wrong and caused a false gate
pass, so trust these names, not memory:

1. **Existing Research Before Building** (NON-NEGOTIABLE) — survey prior art before adding tools.
2. **Synthesis Verification** — verify >5-claim summaries against source; one disconfirmation search.
3. **Safe Destructive Operations** (NON-NEGOTIABLE) — dry-run + explicit scoped confirmation for
   `rm -rf`, force-push, `reset --hard`, `branch -D`, `clean -f`, drops; no `--no-verify` unasked.
4. **Changelog Discipline** — update `CHANGELOG.md` `[Unreleased]` after any meaningful change.
5. **Progressive Disclosure** — context files under 300 lines; deep docs by pointer; no committed
   auto-generated context files. (This is why the full constitution is NOT inlined here.)
6. **Single Source of Truth for Configuration** — every config field resolves through the one
   resolver; no stray `os.environ.get`; aliases emit deprecation warnings.

Engineering constraints: Stable Public API (Anthropic + OpenAI compat, backward-compatible within
major); No Secrets in Git-Tracked Files (`${VAR}` refs only, warn on literal key patterns);
Deprecation Over Hard-Cut (alias/shim for one release cycle).

**MANDATORY (survives compaction):** Before running any `/speckit.*` command, editing a `plan.md`
Constitution Check, or marking tasks complete, you MUST Read `.specify/memory/constitution.md` in
full. The names above are for drift detection only; the file body is the source of truth.

## Spec-Driven Development

Active feature specs live under `specs/NNN-feature-name/`. The current feature is
`specs/003-model-scan-integration/` (requirements.md, design.md, spec.md, plan.md, research.md,
data-model.md, contracts/, tasks.md).

### Rules for processing tasks.md correctly

1. **Gate first.** `plan.md` MUST contain a `Constitution Check` that enumerates **every `### `
   principle heading in `.specify/memory/constitution.md`** by name (currently six) with PASS /
   FAIL / N/A + justification. If it lists fewer than the file defines, or lists items that are
   not constitution principles (e.g. "no hardcoded model names", "reuse over duplication"), the
   gate is INVALID — fix `plan.md` before any implementation. Re-run the gate after Phase 1 design.
2. **Phase order is binding.** Phase 0 precedes all. Phase 1 (model-scan) and Phase 2 (router) may
   run in parallel only after the contract tasks T001–T004 are fixed. Phase 3 needs Phase 2;
   Phase 4 needs Phase 3; Phase 5 needs Phase 2 + the T050 spike; Phase 6 needs Phase 4; Phase 7
   needs Phase 1.
3. **MVP boundary.** US1 + US2 (Phases 0–4) is the first shippable increment. Do not pull US4/US5/
   US6 work forward into the MVP unless explicitly asked.
4. **`[P]` tasks** touch distinct files with no dependency and may run together; non-`[P]` tasks in
   a phase are sequential.
5. **Per-task obligations.** Any task with a `SC-*` success criterion needs at least one test
   before it is declared complete (Principle: Test Expectations). Tasks touching teardown,
   atomic swaps, or alias installation (T023, T042, T046) invoke Principle III — confirm scope.
   Finish with T086: update `CHANGELOG.md` and `docs/` (Principle IV).
6. Run `/speckit.implement` to execute the list, but only after the gate in rule 1 passes.
