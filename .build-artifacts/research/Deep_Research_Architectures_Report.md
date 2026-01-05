# Deep Research Architectures: Comparative Analysis & Implementation Strategy

## Executive Summary
This report unifies findings from an analysis of major AI provider capabilities (Gemini, OpenAI), open-source agent architectures (LangChain, wshobson, agentic-flow), and specific user requirements for a new "Deep Research" skill. The goal is to define a robust, multi-level research agent that balances breadth (multiweb search) with depth (targeted retrieval) and grounding (GitHub/Social validation).

## Analysis of Existing Architectures

### 1. Gemini Deep Research
*   **Core Philosophy**: Asynchronous, long-running (up to 30 mins) orchestration.
*   **Mechanism**: Separates "Planning" (Query Decomposition) from "Execution" (Parallel Search).
*   **Key Feature**: "Continuous Reasoning Loop" that iterates based on intermediate findings.
*   **Strength**: Highly structured, detailed feasibility studies (as seen in *Project Keychain* comparison).

### 2. Open Source Ecosystem
*   **Hierarchical Reasoning**: Most advanced agents (e.g., `wshobson/agents`) use a 3-tier model:
    1.  **Strategic**: Planning & Decomposition (e.g., Claude Sonnet, GPT-4).
    2.  **Orchestrator**: Sub-task management.
    3.  **Execution**: Tool usage (e.g., Haiku, DeepSeek) for scraping/searching.
*   **Cost Optimization**: "Agentic Flow" patterns route simple tasks to cheaper models.
*   **Consensus Protocols**: Systems like `openrouter-deep-research-mcp` use "MSeeP" to triangulate facts from multiple sources.

## Data-Driven Algorithm for New Skill
Based on the analysis, the new `deep-research` skill implements a deterministic Tiered Complexity Logic:

| Metric | Level 1 (Probe) | Level 2 (Standard) | Level 3 (Deep) | Level 4 (Omniscient) |
| :--- | :--- | :--- | :--- | :--- |
| **X (Decomposition)** | 3 Items | 6 Items | 12 Items | 20+ Items |
| **Y (Multiweb Breadth)** | 1 Search | 3 Searches | 6 Searches | 10+ Searches |
| **Z (Targeted Depth)** | 0 Retrievals | 2 Retrievals | 4 Retrievals | 8+ Retrievals |
| **Grounding (Sources)** | Optional | ~10 Sources | ~20 Sources | Max Coverage |

## Grounding & Validation Strategy
A critical gap in tailored research is "Prior Art" detection. The new skill mandates:
*   **GitHub**: Specific tool-use to find code repositories (Min 10 sources).
*   **Social**: Targeted searching of Reddit/X to gauge community sentiment and "in-the-wild" usage.
*   **Iterative Validation**: A strict user-feedback loop ("Is this acceptable?") prevents premature completion.

## Conclusion
The implemented `deep-research` skill successfully hybridizes the structural rigor of Gemini's planner with the breadth/speed of open-source swarm agents. By strictly defining X, Y, and Z parameters, it offers predictable cost/performance tradeoffs while ensuring deep "grounding" in code and community context.
