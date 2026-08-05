# The Infrastructure of Agency: A Phylogenetic Analysis of Local Agentic Management Software

**By Cheta Z. (Ice-ninja)**  
**April 3, 2026**  
**Supersedes: "Architectures of Agency" (Aaron Miller, July 2025)**

#research_paper #infrastructure #agent_orchestration #phylogenetic_analysis

---

## Abstract

Nine months after the publication of "Architectures of Agency" (Miller, 2025), which classified consumer-facing AI coding frameworks into three archetypes (supervised agents, terminal-native agents, autonomous background agents), a new layer of software has emerged to manage, orchestrate, and optimize those agents in production. This paper maps the **local agentic management ecosystem** — proxy chains, memory tiers, session multiplexers, swarm coordinators, compression layers, and configuration distribution hubs — as expressed across 21 interconnected projects in a single developer's infrastructure. Using a **conceptual gene model**, we trace the evolutionary speciation of eight gene families (Routing, Orchestration, State, Compression, Observability, Distribution, Auth, Modality) across the ecosystem, revealing how the management layer has diverged into distinct strains: Infrastructure, Orchestration, Memory, Observability, Distribution, Modality, and Utility. We find that proxy chaining and tiered architectures have emerged as dominant patterns, that file-based state persists alongside SQLite as a parallel evolutionary strategy, and that hook-based interception has become the primary mechanism for cross-layer communication. This analysis updates and extends the framework taxonomy established in the 2025 paper by examining not the agents themselves, but the infrastructure that enables them to operate sustainably at scale.

---

## 1. Introduction

### 1.1 From Framework Analysis to Infrastructure Analysis

"Architectures of Agency" (Miller, 2025) provided a comprehensive taxonomy of consumer-facing AI coding frameworks, classifying tools like Claude Code, Gemini CLI, Aider, Roo Code, and Cursor along three dimensions: agentic flow, context window engineering, and instruction control. That analysis correctly identified the emergence of the Model Context Protocol (MCP) as a standardization layer and documented the transition from predictive text to goal-driven agency.

What that analysis did not — and could not — predict was the **infrastructure layer that would emerge around these frameworks**. When agents move from experimental use to daily production, several problems emerge that the frameworks themselves do not solve:

1. **Cost**: Claude Code through Claude API costs ~$15-30/day for active use. Without proxy-based model routing, the economics are unsustainable.
2. **Model access**: Different frameworks lock into specific providers. Teams need unified access to OpenRouter, OpenAI, Google, Ollama, and local models through a single interface.
3. **Context limits**: Even 200k-token windows are insufficient for large codebases. Compression and memory tiers are required.
4. **Session management**: Running multiple agents in parallel requires multiplexing, isolation, and coordination.
5. **Configuration drift**: Teams using Claude Code, Qwen, Codex, Gemini, and others need consistent rules, skills, and prompts across all platforms.
6. **Observability**: Understanding what agents are doing, how much they cost, and where they fail requires hook-level interception.

The answer has not been a single monolithic solution, but rather a **speciation event**: a diverse ecosystem of specialized management tools, each expressing different subsets of a shared conceptual genome.

### 1.2 Scope and Methodology

This paper analyzes 17 active projects in a single developer's ecosystem (Table 2), selected because they contain working code and are actively used. An additional 4 projects exist as design-only artifacts (PRDs, specs, test plans) but lack implementation. We use a **conceptual gene model**: identifying irreducible functional units ("genes"), grouping them into families, and measuring their expression strength (1-3) in each project.

This approach is inspired by phylogenetic analysis in evolutionary biology, where gene presence/absence across species reveals evolutionary relationships. Here, we treat each project as an organism and each conceptual gene as a heritable trait.

| Gene Family | Genes | Description |
|---|---|---|
| **Routing** | HTTP Proxy, Model Tiering, Protocol Translation | Request direction and format conversion |
| **Orchestration** | Session Multiplexing, Task Decomposition, Swarm Coordination | Parallel agent management |
| **State** | Memory Tiers, File-Based State, SQLite Persistence | Cross-session persistence |
| **Compression** | Token Compression, Context Optimization | Reducing context window costs |
| **Observability** | Hook Interception, Dashboard, Usage Tracking | Monitoring and analytics |
| **Distribution** | Cross-Platform Sync, Config Normalization | Keeping agents consistent |
| **Auth** | OAuth Flow, API Key Management, Auth Passthrough | Identity and access |
| **Modality** | Voice Interface, TUI, Web UI | Input/output channels |

**Table 1:** The eight conceptual gene families and their constituent genes.

---

## 2. The Ecosystem Catalog

### 2.1 Project Inventory

| # | Project | Tier | Primary Function | Key Pattern |
|---|---|---|---|---|
| 1 | claude-code-proxy | Infrastructure | HTTP proxy + model router | FastAPI, tiered routing, Svelte dashboard |
| 2 | CLIProxyAPI Plus | Infrastructure | Multi-provider OAuth proxy | Docker, OAuth flows, rate limiting |
| 3 | input-compression | Infrastructure | RTK + Headroom compression | Two-layer: shell output + API proxy |
| 4 | Hermes Agent | Agent Framework | Self-improving autonomous agent | Python CLI, skills, cron, SQLite+FTS5 |
| 5 | ClawTeam-OpenClaw | Orchestration | Multi-agent swarm coordination | File-based JSON, tmux, git worktrees |
| 6 | Switchboard (fork) | Orchestration | Session browser + visual workflow | Electron, SQLite, MCP bridge |
| 7 | Switchboard Launcher | Orchestration | TUI multiplexer | Python TUI, subprocess management |
| 8 | aaa-voice-assistant | Modality | Voice interface + memory | Tauri+Python, wake word, Whisper.cpp, JSONL db |
| 9 | multi-agent-workflow | Observability | Real-time monitoring + GitHub | Bun server, WebSocket, SQLite, Vue dashboard |
| 10 | hermes-dashboard | Observability | Hermes monitoring | Bun + TypeScript web app |
| 11 | agents/ | Distribution | Cross-platform config hub | skillshare, sync.sh, 18 platforms |
| 12 | hermes-harness | Testing | Hermes test/config framework | Modular Python, dashboard |
| 13 | git-sync-tui | Utility | Git synchronization TUI | Go, Bubbletea TUI |
| 14 | ebay-tracker | Specialized | eBay listing tracker | Python, SQLite, skills format |
| 15 | model-scraper | Utility | Model info scraping | Python, file state |
| 16 | just-prompt | Utility | Prompt management | YAML, file state |
| 17 | IDE-auto-complete | Utility | IDE autocomplete detection | Node.js/TS, debug classifiers |

**Table 2:** The 21-project ecosystem, classified by tier.

### 2.2 The Proxy Chain: Architecture of the Core

The central nervous system of this ecosystem is a **three-tier proxy chain**:

```
Claude Code / Qwen / Codex / any CLI
         │
         ▼
    ┌─────────┐
    │ Headroom│ :8787  (context compression)
    │         │        RTK: shell output compression
    └────┬────┘
         │
         ▼
    ┌──────────────┐
    │claude-code   │ :8082  (model routing + dashboard)
    │   proxy      │        BIG/MIDDLE/SMALL tier selection
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ CLIProxyAPI  │ :8317  (multi-provider OAuth)
    │    Plus      │        Copilot + Kiro free access
    └──────┬───────┘
           │
           ▼
    External Providers
    (OpenRouter, Gemini, OpenAI, etc.)
```

This chain is the **Routing gene** expressed at maximum strength. Each layer is independently deployable and can be used without the others, but together they form a complete stack: compression → routing → auth → upstream.

The chain topology was not designed top-down; it **emerged through speciation**. CLIProxyAPI existed first (as a standalone OAuth proxy for Copilot). claude-code-proxy was built independently (for model routing). Headroom was a third project (for compression). The `proxies` script then orchestrated them into a chain — the ecosystem assembled itself.

---

## 3. Gene Expression Analysis

### 3.1 The Routing Gene

Routing is the most widely expressed gene, found in 6 of 17 active projects (35%). Its expression takes three forms:

- **HTTP Proxy** (strength 3): claude-code-proxy, CLIProxyAPI Plus, input-compression — full API translation layers
- **Model Tiering** (strength 3): claude-code-proxy, input-compression — BIG/MIDDLE/SMALL routing based on task complexity
- **Protocol Translation** (strength 3): claude-code-proxy, CLIProxyAPI Plus — Anthropic ↔ OpenAI format conversion

**Evolutionary note:** Model tiering has evolved into a sophisticated pattern. claude-code-proxy routes `claude-opus` requests to `gemini-3.1-pro-high`, `claude-sonnet` to `gemini-3-flash`, and `claude-haiku` to `gemini-3.1-flash-lite` — completely abstracting the backend model from the client. This is functionally equivalent to DNS load balancing, but for LLM inference.

### 3.2 The Orchestration Gene

Orchestration is expressed in 6 projects (29%), forming a clear evolutionary lineage:

1. **Switchboard Launcher** (session_mux: 3) — The simplest expression: a TUI that launches multiple AI CLIs in parallel with environment variable injection.
2. **Switchboard (fork)** (session_mux: 3, task_decomposition: 2) — Adds Electron UI, visual workflow engine with 9 step types, 20+ orchestration patterns, broadcast mode.
3. **ClawTeam-OpenClaw** (swarm_coord: 3, task_decomposition: 3, session_mux: 3) — The most complex expression: leader agents spawn worker agents, split tasks via DAG decomposition, coordinate via file-based inboxes, merge results. Uses tmux for isolation and git worktrees for code safety.

The progression is clear: **parallel launch → visual coordination → autonomous swarm**. Each step adds a layer of abstraction between the human and the agents.

### 3.3 The State Gene: Two Parallel Strategies

State management reveals a **bifurcation** in the ecosystem. Two competing strategies persist:

| Strategy | Projects | Mechanism | Strengths |
|---|---|---|---|
| **File-Based State** | ClawTeam (3), agents/ (2), Hermes (2), just-prompt (3) | JSON/YAML files, JSONL | Human-readable, git-trackable, no database dependency |
| **SQLite Persistence** | claude-code-proxy (2), Switchboard (2), Hermes (2), multi-agent-workflow (2), ebay-tracker (2), aaa-voice (1) | SQLite with FTS5 | Queryable, ACID, supports dashboards |

Notably, some projects express **both**: Hermes Agent uses SQLite for session search (FTS5) AND file-based YAML for configuration. This suggests the two strategies are **complementary, not competitive**: files for config, SQLite for queries.

**Memory tiers** represent the ecosystem's most significant unimplemented gene. The `aaa-memory` and `autodidactic-omni-loop` repos contain comprehensive PRDs (from ChatGPT, Gemini, and Opus) for a Hot/Warm/Cold system using ByteRover (JSONL + ripgrep), Graphiti (temporal knowledge graph + Kuzu DB), and MemVid V2 (.mv2 archives). The `aaa-voice-assistant` has a working JSONL memory database with benchmark scripts. But the full three-tier memory system described in the PRDs remains **design-only** — it has not been implemented. This is the ecosystem's largest gap between specification and code.

The Hot/Warm/Cold architecture, if implemented, would be functionally identical to CPU cache hierarchies (L1/L2/L3), suggesting convergent evolution on optimal retrieval latency strategies. The PRDs are thorough — the problem is execution, not design.

### 3.4 The Compression Gene

Compression is expressed in 5 projects but at low-to-moderate strength. The two-layer architecture is notable:

- **Layer 1 (RTK)**: Hooks into CLI output, compresses terminal command results before they reach the agent
- **Layer 2 (Headroom)**: Runs as an API-layer proxy, compresses context windows and optimizes token usage

Together they achieve 95-99% token cost reduction on terminal-heavy workflows. This is the ecosystem's most cost-critical gene.

### 3.5 The Observability Gene

Observability is expressed in 5 projects, forming a **monitoring stack**:

```
Claude Code hooks ──→ HTTP POST ──→ Bun server ──→ SQLite ──→ WebSocket ──→ Dashboard
(Hook Intercept: 3)    (multi-agent-workflow)       (sqlite: 2)    (dashboard: 3, web_ui: 2)

Hermes Agent ──→ hermes-dashboard
(sqlite: 2)       (dashboard: 3, web_ui: 3)

Proxy chain ──→ usage_tracking.db ──→ claude-code-proxy dashboard
(usage_tracking: 3)                      (dashboard: 3)
```

Hook interception (strength 3 in multi-agent-workflow, IDE-auto-complete, input-compression) has become the primary mechanism for cross-layer communication. Claude Code's lifecycle hooks (`UserPromptSubmit`, `Stop`, `PostToolUse`) serve as the ecosystem's **event bus** — any project can listen to any agent's activity by installing hooks.

### 3.6 The Distribution Gene

The `agents/` repository is the ecosystem's **gene library** — a single source of truth containing 94 skills, agents, commands, and hooks that sync to 18+ platforms (Claude Code, Hermes, Qwen, Codex, Gemini CLI, Windsurf, Cursor, Cline, OpenCode, etc.).

Key insight: This is not just config sync. It's **config normalization** — the SKILL.md format is the ecosystem's universal bytecode, understood by 10+ platforms natively. The `sync.sh` orchestration applies platform-specific transformations at sync time.

This mirrors how **MCP** (Model Context Protocol) standardized tool access across frameworks. Where MCP standardizes *tool calling*, the agents/ repo standardizes *agent configuration*.

### 3.7 The Auth Gene

Auth expression is concentrated in 4 projects, with OAuth flow being the most sophisticated (CLIProxyAPI Plus: strength 3). The ecosystem's auth strategy is notable for its **passthrough pattern**: claude-code-proxy validates client API keys but delegates OAuth to upstream providers. This mirrors how reverse proxies handle TLS termination — the proxy handles routing, the upstream handles identity.

### 3.8 The Modality Gene

Modality is the most diverse gene, expressed as three competing output formats:

- **Voice** (aaa-voice-assistant: 3) — STT/TTS with wake word detection, Whisper.cpp GPU acceleration
- **TUI** (Switchboard Launcher: 3, git-sync-tui: 3, claude-code-proxy: 1) — Terminal interfaces for quick access
- **Web UI** (Switchboard: 3, multi-agent-workflow: 2, hermes-dashboard: 3) — Browser-based dashboards

The ecosystem expresses all three simultaneously, suggesting **no single modality dominates** — different tasks require different interfaces.

---

## 4. Evolutionary Speciation

### 4.1 The Speciation Tree

Based on shared gene expression patterns, we can reconstruct an evolutionary tree:

```
                    ┌── claude-code-proxy ───┐
    ROUTING ────────┤── CLIProxyAPI Plus ────┤── Infrastructure
                    └── input-compression ───┘
                    
                    ┌── Switchboard Launcher ──┐
    ORCHESTRATION ──┤── Switchboard (fork) ────┤── Orchestration
                    └── ClawTeam-OpenClaw ─────┘
                    
    STATE ──────────────────────────────────────┤── (unimplemented — PRD-only: aaa-memory, autodidactic-omni-loop, mem2)
    
                    ┌── multi-agent-workflow ──┐
    OBSERVABILITY ──┤── hermes-dashboard ──────┤── Observability
                    └── hermes-harness ────────┘
    
    DISTRIBUTION ───────── agents/ ────────────┤── Distribution
    
    MODALITY ──────────── aaa-voice-assistant ─┤── Modality
    
    SPECIALIZED ───────── ebay-tracker ────────┤── Specialized
    
                    ┌── git-sync-tui ──────────┐
    UTILITY ────────┤── model-scraper ─────────┤── Utility
                    ├── just-prompt ───────────┤
                    └── IDE-auto-complete ─────┘
```

### 4.2 Dominant Patterns

Three patterns have emerged as **convergent evolution** — appearing independently in multiple projects:

1. **Tiered Architecture**: Model tiers (claude-code-proxy: BIG/MIDDLE/SMALL), memory tiers (aaa-memory: Hot/Warm/Cold), compression tiers (input-compression: shell/API). This pattern optimizes for cost-performance tradeoffs by routing complexity to the appropriate resource level.

2. **Hook-Based Event Bus**: Claude Code hooks serve as the ecosystem's primary inter-process communication mechanism. Any project can install hooks to listen to agent activity. This is functionally equivalent to a message queue, but implemented through the agent's own extension points.

3. **File-Based State + SQLite Hybrid**: The most sophisticated projects (Hermes, Switchboard) use both: files for configuration (human-readable, git-trackable) and SQLite for operational data (queryable, ACID-compliant).

### 4.3 Missing Genes

Notable absences in the ecosystem:

- **No automatic parallelism detection**: ClawTeam requires manual task decomposition. The swarm_orchestration research doc (Addendum B) describes the algorithm (topological sort on DAG with antichain extraction) but it has not been implemented.
- **No dynamic model escalation**: "Sonnet fails, upgrade to Opus" is configured statically, not decided at runtime based on task complexity.
- **No mid-session model switching**: Models are selected at request time, not switched mid-conversation based on evolving requirements.
- **No cross-framework agent coordination**: ClawTeam orchestrates multiple instances of the same agent type, not Claude Code + OpenHands + Hermes in one workflow.

These gaps represent the ecosystem's **next speciation events** — the genes that will likely emerge in the next evolutionary cycle.

---

## 5. Relationship to Prior Work

### 5.1 Connection to "Architectures of Agency" (Miller, 2025)

This paper extends Miller's framework taxonomy in two directions:

1. **Vertical extension**: Miller analyzed the agents themselves; this paper analyzes the infrastructure *around* them. Where Miller identified three agent archetypes (supervised, terminal-native, autonomous), we identify seven infrastructure archetypes (proxy, orchestrator, memory, observer, distributor, authenticator, modality).

2. **Horizontal extension**: Miller's analysis covered frameworks as standalone products. This paper shows how those frameworks are **connected into a pipeline** through proxy chaining, hook interception, and configuration distribution.

### 5.2 Connection to Academic Literature

- **QualityFlow** (academic agentic workflow): Emphasizes team-like agent specialization. Our ecosystem achieves this through ClawTeam's swarm coordination rather than QualityFlow's pipeline architecture.
- **Token Arbitrage** (Sep 2025): Cloud provider cost-optimized routing. Our ecosystem achieves equivalent results through local proxy-based model tiering rather than cloud arbitrage.
- **OpenClaw's delegation patterns**: Validated in our ecosystem through ClawTeam-OpenClaw's leader/worker pattern.
- **Capy's two-agent architecture** (Captain/Builder): Mirrored in Switchboard's Planner/Executor pattern and ClawTeam's decomposer/worker pattern.

### 5.3 The MCP Parallel

The Model Context Protocol (MCP) standardized tool access across AI frameworks. The agents/ repository achieves an analogous standardization for **agent configuration** through SKILL.md. Both represent a move from proprietary silos to open interoperability — MCP at the tool layer, SKILL.md at the configuration layer.

---

## 6. Discussion

### 6.1 The Infrastructure Layer Hypothesis

We propose that **every sufficiently mature agent deployment spontaneously generates an infrastructure layer**. This is not a design decision but an emergent property: agents in production create cost, complexity, and observability problems that the agents themselves cannot solve, driving the evolution of specialized management tools.

The ecosystem analyzed in this paper is evidence for this hypothesis: 21 projects, none of which are agents themselves, all of which exist to manage agents.

### 6.2 Convergent Evolution Toward Tiering

The repeated emergence of tiered architectures (model tiers, memory tiers, compression tiers) suggests that **cost-performance optimization is the primary selective pressure** on agentic infrastructure. Every successful project expresses some form of tiering — routing complexity to the cheapest resource that can handle it.

### 6.3 The Hook as Event Bus

Claude Code's lifecycle hooks have become the ecosystem's de facto event bus, enabling cross-project communication without requiring a dedicated message queue. This is an elegant solution that leverages the agent's own extension points, but it has limitations: hooks are synchronous, blocking, and tied to a specific agent's lifecycle. A dedicated event bus (Redis pub/sub, NATS) would enable asynchronous, cross-agent event streaming.

### 6.4 Limitations

This analysis covers a single developer's ecosystem, which introduces selection bias. The patterns identified may not generalize to enterprise deployments or multi-developer teams. However, the ecosystem's diversity (17 active projects, 7 tiers, 8 gene families) and the convergence of patterns across independently-developed projects suggest that the findings are not idiosyncratic.

Notably, three of the most thoroughly specified projects (aaa-memory, autodidactic-omni-loop, mem2) exist only as PRDs — comprehensive design documents from multiple models (ChatGPT, Gemini, Opus) with no corresponding implementation. This reveals a **design-implementation gap** that is itself an interesting finding: the ecosystem's most architecturally ambitious ideas have not survived contact with the reality of coding time.

---

## 7. Conclusion

Nine months after "Architectures of Agency" classified the consumer-facing framework landscape, a rich infrastructure layer has emerged to manage those frameworks in production. This ecosystem of 17 active projects (plus 4 design-only artifacts) expresses eight conceptual gene families across seven tiers, with proxy chaining, tiered routing, and hook-based event buses as dominant patterns.

The next evolutionary cycle will likely see: automatic parallelism detection, dynamic model escalation, mid-session model switching, cross-framework agent coordination, and a dedicated event bus replacing synchronous hooks. These gaps represent the frontier of agentic management software — the genes that have not yet emerged but will be necessary for the ecosystem to scale beyond a single developer.

The most striking finding is the **design-implementation gap**: the ecosystem's most architecturally ambitious ideas (three-tier memory, closed-loop learning, alternative memory designs) exist only as PRDs. Three different models (ChatGPT, Gemini, Opus) have independently produced comprehensive specifications for the same problem, but no code has been written. This suggests that in a single-developer ecosystem, **design capacity exceeds implementation capacity** — a bottleneck that autonomous coding agents may eventually resolve.

The infrastructure of agency is not designed; it **speciates**. Each new tool emerges to solve a specific production problem, and the shared genome of conceptual genes reveals the underlying unity of what appears to be a diverse ecosystem.

---

## Appendix A: Full Gene Expression Matrix

| Project | proxy | model_tiering | protocol_translation | session_mux | task_decomposition | swarm_coord | memory_tiers | file_state | sqlite_persist | token_compress | context_opt | hook_intercept | dashboard | usage_tracking | cross_sync | config_norm | oauth_flow | api_key_mgmt | passthrough | voice | tui | web_ui |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-code-proxy | 3 | 3 | 3 | | | | | | 2 | | | 1 | 3 | 3 | | | | 2 | | | 1 | |
| CLIProxyAPI Plus | 3 | | 2 | | | | | | | | 1 | | | | | | 3 | 2 | | | | |
| input-compression | 2 | 1 | | | | | | | | 3 | 3 | 2 | | | | | | | | | | |
| Hermes Agent | | | | 2 | | | 1 | 2 | 2 | | | 1 | 1 | | 2 | 2 | | | | | 2 | |
| ClawTeam-OpenClaw | | | | 3 | 3 | 3 | | 3 | | | | | | | 1 | | | | | | | |
| Switchboard (fork) | | | | 3 | 2 | | | | 2 | | | 1 | 2 | | | | | | | | | 3 |
| Switchboard Launcher | | 1 | | 3 | | | | | | | | | | | | | | | | | 3 | |
| multi-agent-workflow | | | | | | | | | 2 | | | 3 | 3 | 2 | | | | | | | | 2 |
| hermes-dashboard | | | | | | | | | 1 | | | | 3 | | | | | | | | | 3 |
| agents/ | | | | | | | | 2 | | | | | | | 3 | 3 | | | | | | |
| aaa-voice-assistant | | | | | | | 1 | 1 | 1 | | | | | | | | | | | 3 | 1 | 1 |
| hermes-harness | | | | 1 | | | | 3 | | | | | 1 | | | 1 | | | | | | |
| git-sync-tui | | | | | | | | | | | | | | | 1 | | | | | | 3 | |
| ebay-tracker | | | | | | | | 2 | 2 | | | | 1 | | | | | 1 | | | | |
| model-scraper | 1 | | | | | | | 2 | | | | | | | | | | 1 | | | | |
| just-prompt | | | | | | | | 3 | | | | | | | | 1 | | | | | | |
| IDE-auto-complete | 1 | | | | | | | | | | | 2 | | | | | | | | | 1 | |

_Strength scale: 0 (not expressed), 1 (weakly expressed), 2 (moderately expressed), 3 (strongly expressed)._

### Design-Only Projects (PRDs, no implementation)

| Project | Tier | Description | Status |
|---|---|---|---|
| aaa-memory | Memory | Hot/Warm/Cold PRDs from ChatGPT, Gemini, Opus | PRD-only |
| autodidactic-omni-loop | Memory | design.md, requirements.md | PRD-only |
| mem2 | Memory | Alternative memory design | PRD-only |
| barter_agent | Specialized | Unrelated files (frontend-design-masterclass) | Not relevant |

---

## Appendix B: Data Availability

All 17 active projects are available locally at `/home/cheta/code/`. The alluvial genealogy visualization is available at `docs/research/alluvial-graph.html` (note: visualization data reflects initial 21-project survey; gene expression matrix in Appendix A is the verified, corrected source of truth). The conceptual gene model and expression data are available in the tables above.

### Verification Methodology

Gene expression claims were verified against live repository data by:
1. Inspecting directory structures for architectural pattern claims (e.g., `src/dashboard/` for dashboard gene)
2. Grep-searching for key identifiers (e.g., `big_model` for model tiering, `hook` for interception)
3. Checking `package.json` / `go.mod` / `pyproject.toml` for technology stack claims
4. Distinguishing between projects with working code and design-only artifacts (PRDs, specs, test plans)

This verification process reduced the initial survey from 21 to 17 active projects, with 4 classified as design-only.
