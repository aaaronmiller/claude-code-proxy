# Competitor Analysis: Deep Research Agents

## Overview
This document benchmarks the custom `deep-research` skill against leading open-source alternatives identified on GitHub. The goal is to establish where our skill stands in terms of features, complexity, and rigor.

## Top Competitors

### 1. GPT Researcher (`assafelovic/gpt-researcher`)
*   **Status**: The "Gold Standard" implementation.
*   **Architecture**: "Planner" agent generates questions -> "Execution" agents search in parallel -> "Reviewer" synthesizes.
*   **Key Features**:
    *   Aggregates 20+ web sources.
    *   Generates 2000+ word reports.
    *   Exports to PDF, Docx, MD.
    *   Local document support.
*   **differentiation**: Highly application-focused (web UI), less "agentic skill" and more "platform".

### 2. LangChain Open Deep Research (`langchain-ai/open_deep_research`)
*   **Status**: Advanced, modular reference implementation.
*   **Architecture**: Built on **LangGraph**. Uses a State Graph for "Plan -> Web Search -> Reflection -> Refinement".
*   **Key Features**:
    *   Recursive depth (loops back if info is insufficient).
    *   Human-in-the-loop (interrupt before final report).
    *   MCP integration.

### 3. Deep Research Agent (`tarun7r/deep-research-agent`)
*   **Status**: Specialized implementation.
*   **Key Features**:
    *   **Credibility Scoring**: Explicitly rates sources to reduce hallucinations.
    *   **4-Agent Swarm**: Planner, Searcher, Synthesizer, Writer.

## Benchmarking Matrix

| Feature | `deep-research` (Ours) | `gpt-researcher` | `langchain-ai` | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Complexity Control** | **Deterministic Levels (1-4)** | Automatic / Adaptive | Graph-based (Loop limit) | **Ours is more predictable** for cost/time control. |
| **Grounding** | **Explicit GitHub/Social mandates** | General Web Search | General Web Search | **Ours wins on specific "prior art" discovery.** |
| **Architecture** | Single-Prompt / Step-by-Step | Multi-Agent / Parallel | State Graph (LangGraph) | **Theirs is more robust** for complex state handling (loops). |
| **Output** | Markdown Report | PDF/Docx/MD | Markdown | **Theirs wins on format variety.** |
| **Verification** | "**Prior Art**" focused | Factual Consensus | Reflection Steps | **Ours is better for Engineering/Dev tasks.** |

## Gap Analysis & Recommendations
1.  **Credibility Scoring**: We lack an explicit step to "rate" sources. We rely on the LLM's inherent judgment.
    *   *Recommendation*: Add a specific instruction in Phase 3 to "assess source credibility".
2.  **Recursive Graph**: We use a linear "Loop" (Phase 5). LangGraph uses a true graph.
    *   *Recommendation*: Refine Phase 5 to be more explicit about *partial* loops (e.g., "return to Phase 2 for just item 3").
3.  **Format Independence**: We only output Markdown.
    *   *Recommendation*: Keep as Markdown for now (Ice-Ninja standard), but ensure structure is "Pandoc-ready".

## Conclusion
The `deep-research` skill is the **"Best" for Developer-Centric Prior Art Research** due to its specific mandates for GitHub/Social grounding and deterministic complexity levels. However, it lacks the raw "platform" features of `gpt-researcher` (PDF export, web UI). It is a "Skill", not an "App", which fits the user's ecosystem perfectly.
