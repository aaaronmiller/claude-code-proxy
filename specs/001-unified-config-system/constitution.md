# Global Rules

## Safety
- NEVER `rm -rf` — use `rmdir` (empty dirs) or `rm` with explicit paths
- Destructive commands (rm, delete, drop, reset, force-push): show dry-run, ask first
- No wildcards with `rm` unless user approves

## Terminal
- ALWAYS specify terminal: **WSL/bash**, **PowerShell (Admin)**, or **PowerShell**

## User
- Hates Windows nags and "security" warnings
- Never pays for software
- WSL2 (Ubuntu) on Windows 11 Canary, HP Spectre 16" 2023




## Existing Research Mandate

Before starting any project, tool, or capability, I MUST research existing solutions.

**Trigger:** Any time the user describes a new project, tool, or capability to build.

**Minimum research (floor, not ceiling):**
1. **Local workspace first** — Check for existing agent configs: .claude/, .cursor/, .agents/, skills/, .skillshare/, .kiro/, .windsurf/, .openclaw/, ~/.config/hermes/
2. **Skill registries** — Check skills.sh and agentskills.io for existing skill packages
3. **Code search** — Search GitHub for existing open-source projects solving the same problem

**Additional research as appropriate:**
- npm/PyPI/crates.io for libraries
- arxiv/Google Scholar for research papers
- Community lists (awesome-*) for curated alternatives

**If existing tools are found:**
- Surface them to the user immediately with comparison to the proposed approach
- Do not assume the user's proposed approach is superior without explicit evaluation

**Minimum is a floor, not a ceiling.** If results are partial or ambiguous, continue searching until confident no existing solution fits.

**On failure:** If a known existing project is later discovered to have been missed, document: what was missed, when it was discovered, and why it matters.

---

## Synthesis Verification Mandate

After synthesizing or summarizing complex source material, I MUST verify the synthesis is faithful to the source.

**Trigger:** Any time I produce a summary, transformation matrix, comparison table, or synthesized conclusion from source material exceeding ~5 key claims.

**Verification technique:**
1. **Identify the 3 most consequential claims** — The claims I'm asserting with highest confidence, not the nuanced details
2. **Verify each against the source** — Read back the specific source lines that support or contradict each claim
3. **Check for conflation** — Did I accidentally merge two concepts from the source? Did I attribute a finding from one platform to another?

**Disconfirmation search (apply selectively):**
- Only on high-confidence **factual assertions** (e.g., "X supports Y format")
- Not on nuanced interpretations or conclusions
- Use 1 targeted web search to find evidence that could prove the claim wrong

**What counts as a failure:**
- A synthesized claim that directly contradicts the source material
- A platform attribution error (claiming feature X for platform Y when source says otherwise)
- Missing a well-known alternative that was clearly in the search results

**On failure:** Document the miss — write a brief note: what was asserted incorrectly, what the source actually said, and the specific mechanism of the error (e.g., "conflated progressive disclosure with disable-model-invocation").

## Project Purpose

This repo manages a curated collection of Claude Code/Hermes Agent/Qwen Code plugin extensions:
- **skills/** — SKILL.md directories with YAML frontmatter (task handbooks)
- **agents/** — Subagent YAML configurations
- **commands/** — Slash command definitions
- **hooks/** — Event handler configurations
- **Settings** — Platform-specific configuration

Synced to: Claude Code (~/.claude/), Hermes Agent (~/.hermes/), Qwen Code (~/.qwen/).

---

## Skills Ecosystem

**Discovery:** Browse available skills at https://skills.sh

**skillshare** (installed at `/usr/local/bin/skillshare`, v0.17+) — our skills sync manager.
- `skillshare sync` — sync all skills to 7 configured targets (claude, hermes, qwen, codex, kilocode, openclaw, opencode, gemini)
- `skillshare audit` — scan skills for prompt injection and data exfiltration
- `skillshare extras` — sync rules/commands (non-skill resources) to agent directories
- `skillshare init` — initialize skillshare (source: `~/code/agents/skills`)
- skillshare source: `~/.config/skillshare/`, config: `~/.config/skillshare/config.yaml`

**Skills management scope:** Full ecosystem tool compared to skills-only tools:
| Tool | Scope | Targets | Notes |
|------|-------|---------|-------|
| **skillshare** | Skills + extras (rules/commands) | 56+ | Go CLI, symlinks or copy, audit, team sync |
| **skills.sh** (vercel-labs) | Skills only | 36+ | npx-based, install from GitHub |
| **skm** (reorx) | Skills only | 6+ | Python CLI, YAML-driven |
| **nnnggel/skills** | Skills only | 6+ | TS CLI |

**SKILL.md** is the most portable format — supported natively by 10+ platforms (Claude Code, Hermes, Qwen, Codex, Gemini CLI, Windsurf Cascade, Cursor, Cline, Letta, OpenClaw, KiloCode, OpenCode) with zero transformation. **AGENTS.md** is the cross-platform context file standard (governed by Linux Foundation/Agentic AI Foundation) read natively by Zed, Cline, Windsurf, Codex, Roo, Continue, Augment, and 30+ others. Claude Code does NOT natively read AGENTS.md (feature request #34235 open since 2025, 2100+ upvotes).

**Skills auto-activation reliability:** ~50% baseline, rises to **100% with directive frontmatter** (`ALWAYS invoke when...`). Standard descriptions drop to 37% with hooks. Vercel agent evals: AGENTS.md achieved 100% pass rate, skills achieved 53% default / 79% with explicit prompting. ETH Zurich study (Feb 2026): LLM-generated context files harm performance (-3%), human-written slightly help (+4%). Recommendation: <300 lines, non-inferable details only.

**Sync architecture:** `./sync.sh` is the master orchestrator:
1. `skillshare sync` — skills → all targets (symlinks on Linux)
2. `sync.sh --agents-changelog` — agent subagent change detection (never overwrites edits)
3. `sync.sh --fix` — full sync: skills + agents + CLAUDE.md + hooks + memories + Windows IDE copies

**Windows IDEs** (Kiro, VS Code) use copies not symlinks — no NTFS symlink support. Windows sync skips populated directories to preserve edits from other agents.

**plans/** is local scratch only — omit from sync.

---

## Changelog Mandate

All projects MUST maintain a `CHANGELOG.md` in the project root. After implementing features, fixing bugs, or completing significant work:
1. Update `CHANGELOG.md` under the `[Unreleased]` section with a clear summary of what changed
2. Group entries under `### Added`, `### Fixed`, `### Changed`, or `### Removed`
3. When a release is cut, move `[Unreleased]` entries to a versioned section with the date
4. Keep entries concise but descriptive — one line per change

---

## Progressive Disclosure

When creating or modifying project documentation or skills:
- Keep AGENTS.md concise (<300 lines) — pointers not copies
- Detailed operational docs → separate files, referenced from AGENTS.md
- Code style → linters/formatters, not rules files
- Don't auto-generate context files

---

## Shell Reference (~/.zshrc)

**Functions:** `portsscan`, `mkcd`, `up`, `t` (tree), `logview`, `proj` (fzf project picker), `cutz`/`macros` (help), `sha` (hash compare), `gacp`/`ganp`/`ginit`/`ginitplus` (git workflows), `showbigfiles`, `showbigdirs`, `auto_env`, `is_wsl2`, `wsl2win`, `win2wsl2`, `explorer`

**Aliases:** `ls`=eza, `ll`=eza -la, `cat`=bat, `grep`=rg, `find`=fd, `gco/gst/gpl/gph`=git shortcuts, `pn`=pnpm, `update`=apt+omz, `zsh`=reload, `kiro`=IDE, `ccproxy`=claude proxy, `claude-continue`/`claude-init`=claude CLI
