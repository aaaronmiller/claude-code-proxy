<!--
Sync Impact Report
==================
Version change: (initial template) → 1.0.0
Bump rationale: Initial ratification from empty template. Establishes six principles
and two additional sections derived from repository workflow rules and the current
feature (Unified Configuration System). No prior version to preserve.

Modified principles:  none (initial)
Added sections:
  - Core Principles (I–VI)
  - Engineering Constraints
  - Development Workflow
  - Governance
Removed sections: none

Templates requiring updates:
  ✅ .specify/templates/plan-template.md     — "Constitution Check" gate aligns; no edits needed
  ✅ .specify/templates/spec-template.md     — no constitution references; no edits needed
  ✅ .specify/templates/tasks-template.md    — task categories compatible with principles; no edits needed
  ⚠ .specify/templates/commands/*.md        — directory not installed (user operates via plugin skills);
                                              no local files to reconcile
  ⚠ README.md                               — no explicit constitution link; consider adding a pointer
                                              line (deferred; non-blocking)

Follow-up TODOs:
  - If project was ratified earlier than 2026-04-23, update RATIFICATION_DATE accordingly.
  - Optionally add a one-line pointer to this file from README.md for discoverability.
-->

# Claude Code Proxy Constitution

## Core Principles

### I. Existing Research Before Building (NON-NEGOTIABLE)

Before proposing any new tool, capability, or project addition, authors MUST survey existing
solutions: (1) the local workspace for prior agent configs, skills, and subagents; (2) public
skill registries (skills.sh, agentskills.io); (3) GitHub for open-source projects solving the
same problem. When an existing tool is found, it MUST be surfaced with an explicit comparison
to the proposed approach; the new approach is assumed inferior until the comparison demonstrates
otherwise.

**Rationale**: The project history shows repeated near-duplication of capabilities that already
existed. Research is the cheapest form of de-duplication.

### II. Synthesis Verification

Any synthesis, comparison matrix, or summary asserting more than five key claims about external
material MUST be verified against its source before publication. The top three most consequential
claims MUST be read back to their source lines; conflation and cross-attribution errors MUST be
explicitly checked. High-confidence factual assertions MUST receive one disconfirmation search.

**Rationale**: Summary quality degrades silently under volume. This check is cheap compared to
the cost of acting on a conflated claim.

### III. Safe Destructive Operations (NON-NEGOTIABLE)

Destructive shell operations (`rm -rf`, force-push, `git reset --hard`, database drops,
`checkout --`, `clean -f`, `branch -D`) MUST NOT be invoked without: (a) a dry-run preview, and
(b) explicit user confirmation for the exact scope. Wildcards with `rm` MUST NOT be used unless
the user has approved that specific pattern. `--no-verify` / `--no-gpg-sign` MUST NOT be used
unless the user explicitly requests them. Authorization for a destructive action applies only
to the exact scope approved, not future invocations.

**Rationale**: The cost of pausing to confirm is seconds; the cost of an unwanted destruction
is the work itself. This is the single rule with the highest loss-asymmetry in the project.

### IV. Changelog Discipline

Every project MUST maintain `CHANGELOG.md` in its root. After implementing features, fixing
bugs, or completing significant work, authors MUST update the `[Unreleased]` section with a
one-line entry grouped under `### Added`, `### Fixed`, `### Changed`, or `### Removed`. Released
versions MUST move from `[Unreleased]` into a dated, versioned section.

**Rationale**: Without CHANGELOG discipline, `git log` becomes the only record of intent, and
intent erodes under rebase/squash. Entries are cheap; archaeology is expensive.

### V. Progressive Disclosure

Context files (AGENTS.md, CLAUDE.md, per-directory guidance) MUST stay under 300 lines. Deeper
operational documentation MUST live in separate files referenced by pointer. Code style MUST be
enforced by linters and formatters, not by rules files. Auto-generated context files MUST NOT
be committed.

**Rationale**: The ETH Zurich Feb 2026 study found LLM-generated context files harm performance
(-3%); human-written non-inferable details help (+4%). Length correlates with drift. Shorter
context files survive longer.

### VI. Single Source of Truth for Configuration

Every configuration field MUST be resolvable through exactly one code path (the configuration
resolver). No feature code MAY read values via direct `os.environ.get` or direct JSON mutation
outside the resolver. The persistence surface (stored config file + `.env`) MUST NOT contain
overlapping definitions that could diverge. Legacy environment-variable names MAY be retained
as aliases during deprecation, but MUST emit a deprecation warning identifying the modern
equivalent.

**Rationale**: This project currently has three parallel configuration surfaces (flat env,
structured JSON, argparse) that drift silently. The resolver is the one mechanism that makes
precedence debuggable and surface-parity achievable.

## Engineering Constraints

### Stable Public API

The HTTP surfaces consumed by Claude Code, Qwen Code, and other clients (Anthropic Messages API
compatibility, OpenAI Chat Completions API compatibility) MUST remain backward-compatible within
a major version. Breaking changes MUST be gated behind a major-version bump and a migration
guide committed in the same change.

### No Secrets in Git-Tracked Files

API keys, OAuth tokens, and other credentials MUST NOT be stored as literal values in any file
under version control. Config files MAY reference secrets via `${VAR_NAME}` syntax; the
resolver MUST expand these at read time. When a literal secret format (e.g., a string matching
a known API-key pattern) is detected in a git-tracked config, the system MUST emit a warning.

### Deprecation Over Hard-Cut

When removing a capability, an alias or shim MUST exist for at least one release cycle. The
deprecation window MUST be communicated via warnings that name both the old path and the modern
replacement. Hard cuts without a deprecation window MUST be justified in the plan's
`Complexity Tracking` section.

## Development Workflow

### Spec-Driven Development

New features MUST follow the spec-kit workflow: `spec.md` (what/why) → `plan.md` (how) →
`tasks.md` (atomic work units) → implementation. Skipping phases MUST be justified in the
plan's `Complexity Tracking` section. Every `plan.md` MUST include a `Constitution Check`
section that validates against these principles before proceeding to Phase 0 research and
again after Phase 1 design.

### Multi-Surface Parity

Any configuration field editable via one operator surface (CLI, TUI, web UI, `.env`) MUST be
editable via every surface on which the field is meaningful. Capability asymmetry between
surfaces MUST be flagged in the plan and justified.

### Test Expectations

Tests are not categorically mandatory, but any feature whose spec names a user-facing success
criterion (`SC-*`) MUST have at least one test asserting that criterion. Tests MUST exist
before the feature is declared complete; test-after is acceptable when test-before is not
practical, but test-never is not.

### Branch and Spec Naming

Feature branches and corresponding spec directories MUST share the same numbered slug
(`NNN-short-name`) to satisfy the spec-kit prerequisite checker. Duplicate numbers across
`specs/` directories MUST be resolved before running workflow commands.

## Governance

This constitution supersedes conflicting ad-hoc practices. PR reviews MUST verify compliance
with the six core principles and the two constraint sections. Violations MUST be either fixed
before merge or explicitly justified in the PR description with reference to the principle
being waived.

### Amendment Procedure

Amendments MUST be proposed via a PR that edits `.specify/memory/constitution.md`, increments
`CONSTITUTION_VERSION` per the semver rules below, updates `LAST_AMENDED_DATE`, and prepends a
Sync Impact Report documenting the change.

### Versioning Policy

- **MAJOR**: Backward-incompatible governance changes; principle removal or semantic redefinition.
- **MINOR**: New principle added; new section added; materially expanded guidance.
- **PATCH**: Wording clarifications, typo fixes, non-semantic refinements.

### Compliance Review

Every `plan.md` Constitution Check section MUST enumerate each of the six core principles and
mark status. Unjustified violations MUST block merge.

**Version**: 1.0.0 | **Ratified**: 2026-04-23 | **Last Amended**: 2026-04-23
