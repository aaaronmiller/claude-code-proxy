# Deep Research Skill

## Description
A sophisticated, multi-level research agent designed to perform exhaustive investigation, decomposition, and synthesis of complex topics. This skill mimics the "deliberative refinement" process but applied to information gathering, supporting variable levels of depth from quick probes to omniscient deep dives.

## Activation
- **Triggers**: "deep research", "investigate thoroughly", "comprehensive analysis", "find prior art", "research this"
- **Default Mode**: **Standard** (Level 2) - Balanced depth and breadth.

## Complexity Levels (The Algorithm)
The skill operates on a strict mathematical model of **Decomposition (X)**, **Breadth (Y)**, and **Depth (Z)**.

| Level | Name | X: Search Items | Y: Multiweb Searches | Z: Targeted Retrievals | Grounding (GitHub/Social) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Quick Probe** | 3 Items | 1 Search | 0 Retrievals | Optional |
| **2** | **Standard** (Default) | 6 Items | 3 Searches | 2 Retrievals | Min 10 Sources |
| **3** | **Deep Dive** | 12 Items | 6 Searches | 4 Retrievals | Min 20 Sources |
| **4** | **Omniscient** | 20+ Items | 10+ Searches | 8+ Retrievals | Max Coverage |

## Workflow

### Phase 1: Assessment & Decomposition
1.  **Context Assessment**: Immediately assess any provided source files (e.g., active documents, PDFs).
2.  **Decomposition**: Break the user's request into **X** distinct, atomic search items based on the complexity level.
3.  **Plan Generation**: Create a `research_plan.md` in a temp directory (do not delete unless instructed) outlining the X items and the intended search queries.

### Phase 2: Breadth (Multiweb Search)
1.  **Execution**: Perform **Y** multi-query web searches (`search_web`).
    *   *Rule*: Each "Multiweb Search" should target a cluster of the X items.
2.  **Grounding (Mandatory)**:
    *   **GitHub**: Specifically search GitHub for code, repositories, and prior art.
        *   *Target*: Find at least **10 sources** (Level 2). If successful, expand to 20 or 30 (Level 3/4).
    *   **Social**: Search Reddit, X (Twitter), and Hacker News for specific discussions, "prior art," and community sentiment.
3.  **Logging**: Append all findings, summaries, and URLs to `scratch_findings.md`.

### Phase 3: Depth (Targeted Retrieval)
1.  **Selection**: Identify the top **Z** most promising, high-density sources from Phase 2.
2.  **Retrieval**: Use `read_url_content` (or `browser_snapshot` if highly visual/dynamic) to ingest the **full content** of these Z sources.
3.  **Credibility Check**: Explicitly assess the domain authority, author expertise, and freshness of each source. Flag any potential bias or low-quality signals.
4.  **Analysis**: Deeply analyze this content for specific details, implementation logic, or data points that were missing in the summaries.
5.  **Logging**: detailed notes to `scratch_findings.md` (include credibility flags).

### Phase 4: Unification & Reporting
1.  **Synthesize**: Read `scratch_findings.md` and all assessed local sources.
2.  **Unify**: Merge conflicting data, group related concepts, and build a cohesive narrative.
3.  **Output**: Generate the final artifact (e.g., `Deep_Research_Report.md`) following the structure:
    *   **Executive Summary**: High-level findings.
    *   **Deconstructed Analysis**: Detailed breakdown of the X items.
    *   **Prior Art/Grounding**: Specific section on GitHub/Social findings.
    *   **Source Assessment**: Review of the Z deep-dived sources.
    *   **Conclusion/Roadmap**: Actionable next steps.

### Phase 5: Recursive Validation
1.  **Validation**: Present the summary to the user.
2.  **Loop**: Ask: *"Is this depth acceptable, or should I refine?"*
    *   **If Refine**: Increase complexity level (e.g., Level 2 -> Level 3), KEEP the temp files/scratchpad, and run the process again focusing on gaps.
    *   **If Accept**: Finalize documents and offer to clean up temp files.

## Guidelines
- **Temp Directories**: Use a dedicated subdirectory (e.g., `deep-research/temp/SESSION_ID`) to store all scratch files. **NEVER** delete this directory during the research loop, only after explicit user confirmation.
- **Scratch Files**: Maintain a running log. Do not rely on context window alone.
- **Tools**:
    - Use `search_web` for Breadth.
    - Use `read_url_content` for Depth.
    - Use `find_by_name` / `grep_search` to check local project context for "Grounding" as well.
