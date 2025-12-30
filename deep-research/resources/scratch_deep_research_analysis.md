# Deep Research Skill - Design & Findings Scratchpad

## Research Synthesis

### 1. Existing Deep Research Architectures
**Gemini Deep Research**
- **Core Mechanism:** Asynchronous orchestration backend with separate "Planner" and "Execution" engines.
- **Workflow:** Decompose query -> Plan (User Approval) -> Parallel Execution (Search/Browse) -> Context Management -> Synthesis & Self-Critique.
- **Key Features:** "Continuous reasoning loop", parallelized sub-tasks, state management for long-running queries (up to 30 mins).

**Open Source Models (wshobson/agents, openrouter-deep-research-mcp)**
- **Hierarchical Reasoning:** 3-Tier model (Planning/Strategic -> Coordination/Orchestration -> Execution/Tools).
- **Cost Optimization:** "Agentic Flow" smart routing (e.g. use Haiku/DeepSeek for scraping, Sonnet/GPT-4 for planning).
- **Consensus:** "MSeeP" (Multi-Source Evidence & Evaluation Protocol) - triangulating answers from multiple sources/models.

### 2. User Requirements for New Skill
- **Complexity Levels:** Multiple tiers of depth.
- **Algorithm:** $X$ Search Items, $Y$ Multiweb Searches (Breadth), $Z$ Targeted Retrievals (Depth).
- **Default:** $X=6$ items, $Y=3$ multi, $Z=2$ targeted.
- **Grounding Mandates:**
    - **GitHub:** targeted search for code/prior art (Min 10 sources -> expand to 20/30).
    - **Social:** Reddit/X for discussions/prior art.
- **Workflow:**
    - Use scratch files & temp directories (persistent).
    - "Unification Phase": Merge all documents/findings.
    - Iterative User Feedback Loop.
- **Alignment:** Must align with Anthropic skill definitions.

### 3. Assessment of Provided Sources
*Active Document: `Project Keychain - LLM Deep research comparison.md`*
- **Analysis:** This document serves as a benchmark for the *output quality* expected. It compares distinct AI responses (Gemini, DeepSeek, Perplexity) to a fabrication challenge.
- **Takeaway:** The new skill should aim to replicate the **structure** of the Gemini response (Feasibility, internal assessment, challenges, BOM, roadmap) while utilizing the **breadth** of searching capabilities seen in Perplexity-style agents.

## Implementation Plan: `deep-research` Skill

### Complexity Tiers
| Level | Name | Decomposition (X) | Multiweb Searches (Y) | Targeted Retrievals (Z) | GitHub Checks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Quick Probe** | 3 Items | 1 Search | 0 Retrievals | Optional |
| 2 | **Standard** (Default) | 6 Items | 3 Searches | 2 Retrievals | Min 10 |
| 3 | **Deep Dive** | 12 Items | 6 Searches | 4 Retrievals | Min 20 |
| 4 | **Omniscient** | 20+ Items | 10+ Searches | 10+ Retrievals | Max coverage |

### File Structure
- `SKILL.md`: The core prompt/instruction set.
- `resources/scratchpad_template.md`: Template for the intermediate findings.
- `resources/report_template.md`: Template for the final unified report.

### Logic Flow (Pseudo-Code for Prompt)
1. **Analyze Request**: Determine complexity level (Default to Standard).
2. **Decompose**: Breakdown topic into $X$ sub-questions.
3. **Assessment**: Review any provided files (like `Project Keychain`).
4. **Breath (Multiweb)**:
   - Perform $Y$ searches for the sub-questions.
   - Perform dedicated GitHub/Social searches.
   - *Log findings/urls to scratchpad.*
5. **Depth (Targeted)**:
   - Select top $Z$ URLs.
   - `read_url_content` or `browser_snapshot`.
   - *Append detailed content to scratchpad.*
6. **Unification**:
   - Synthesize all scratchpad data.
   - Write final report.
7. **Loop**: "Are these results acceptable?" -> If no, loop back with refined plan.
