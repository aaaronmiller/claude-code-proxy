# Research Plan: Claude Code -> Gemini Tool Call Transformation
**Session ID:** session_01
**Parameters:** 15 Items / 5 Searches / 3 Deep Dives

## 1. Search Items (Decomposition)
1.  **Claude Code CLI Tool Schema:** definitive JSON schema for `bash`, `repl`, `grep`, `glob` tools expected by Claude Code.
2.  **Gemini API Function Calling Specs:** "prompt" parameter usage in `bash` tool for Gemini models.
3.  **Anthropic vs. Google Tool Protocols:** Comparative analysis of tool definition capability and parameter naming conventions.
4.  **Proxy Transformation Patterns:** Best practices for on-the-fly JSON schema mapping in AI proxies (LiteLLM, OneAPI).
5.  **Streaming JSON Transformation:** Algorithms for robust string replacement in Server-Sent Events (SSE) streams.
6.  **Gemini "Ghost Stream" Phenomenology:** Documentation or community reports of duplicate/empty SSE events in Gemini API.
7.  **Reverse History Normalization:** Strategies for maintaining conversation coherency when upstream/downstream schemas differ.
8.  **Model-Specific Tool Quirks:** `gemini-1.5-pro` vs `gemini-2.0-flash` behavior with "computer use" or code execution tools.
9.  **Token Limit Management:** Handling 1M+ context in proxies designed for 128k limits (Claude Code hardcoded limits?).
10. **Authentication Bridging:** Patterns for adapting OAuth (Google) to API Key (Anthropic) flows in local proxies.
11. **Error Handling & Retries:** standard patterns for masking "403 Forbidden" or "500 Internal Error" from downstream CLIs.
12. **Content-Based Deduplication:** Algorithms for filtering duplicate tool calls in LLM streams.
13. **Claude Code "Superpowers" Internals:** How `superpowers` skill is injected and what specific tool definitions it requires.
14. **Community Solutions:** Existing open-source proxies merging Claude Code with other backends (GitHub, Reddit).
15. **Future-Proofing:** Upcoming Gemini API changes that might impact schema transformation (OpenAI compatibility layer).

## 2. Search Strategy (Breadth)
*   **Search 1 (Schemas & Specs):** "Claude Code CLI tool definition schema", "Gemini API bash tool command vs prompt", "Anthropic tool use json schema".
*   **Search 2 (Proxy & Transformation):** "LLM proxy tool call transformation", "LiteLLM gemini claude compatibility", "streaming json string replacement algorithms".
*   **Search 3 (Gemini Quirks):** "Gemini API duplicate tool description events", "Gemini ghost stream SSE", "Gemini function calling infinite loop fix".
*   **Search 4 (Community & Prior Art):** "Using Gemini with Claude Code CLI", "Claude Code proxy non-anthropic models", "github claude-code-proxy".
*   **Search 5 (Advanced/Edge Cases):** "Gemini 2.0 flash tool use limits", "Injecting user-agent openai client proxy", "reverse normalization llm chat history".

## 3. Targeted Retrieval Candidates (Depth)
*   *To be determined based on search results. Likely targets:*
    *   Official API docs (Google/Anthropic).
    *   Relevant GitHub Issue threads (LiteLLM, Vercel AI SDK).
    *   Detailed technical blog posts on LLM proxying.
