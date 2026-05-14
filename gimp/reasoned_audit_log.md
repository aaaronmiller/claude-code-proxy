# Claude Code Proxy - Reasoned Audit Log

This log tracks my manual, reasoned investigation of each file to understand its useful intent and functional role.

## Batch 2: Services & API (The Nervous System)

### 5. `src/services/prompts/prompt_injector.py`
- **Intent**: Provides "Agent Self-Awareness." It renders proxy metrics into formats injectable into system prompts.
- **Key Logic**: Three-tier rendering (`EXPANDED`, `SINGLE`, `MINI`) ensures compatibility with different context window constraints. It allows the AI to monitor its own "budget" and "health."
- **Reference**: Line 15-180.

### 6. `src/services/models/model_ranker.py`
- **Intent**: An autonomous scraper/ranker that keeps the "Free Tier" competitive.
- **Key Logic**: Integrates with **Exa API** to perform neural web searches for benchmarks. It uses a "Ranker LLM" to process search snippets and assign a `coding_score`.
- **Reference**: Line 40-250.

### 7. `src/api/endpoints.py`
- **Intent**: The primary gateway and "Consistency Manager."
- **Key Logic**: Implements `RequestDeduplicator` to prevent "Ghost Terminal Output" during client retries. It also handles the "VibeProxy" health-checks and token refreshes for the local dev loop.
- **Reference**: Line 100-350.
