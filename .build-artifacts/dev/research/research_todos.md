# Research Plan: Claude Code <> Gemini Transformation Layer Issues

## Objective
Analyze the root causes of protocol mismatches between Claude Code CLI and Gemini (via VibeProxy/Antigravity), specifically focusing on tool call argument mapping (`command` vs `prompt`) and conversation history looping.

## Tasks
- [ ] **Literature Review**: Search for existing documentation, issues, and discussions on:
    - [ ] Claude Code tool call schemas (Bash, etc.)
    - [ ] Gemini tool call schemas (Code Execution)
    - [ ] Middleware/Proxy transformation strategies
    - [ ] "Ghost stream" / duplication issues in SSE proxies
- [ ] **Case Analysis**: Analyze the specific failure modes observed in this session:
    - [ ] `InputValidationError: unexpected parameter 'prompt'`
    - [ ] Infinite tool loops (repetition of successful commands)
    - [ ] Double responses in CLI output
- [ ] **Protocol Mapping**: Document the exact JSON schemas expected by both sides.
- [ ] **Solution Synthesis**: Formulate a robust architectural pattern for bi-directional translation.
- [ ] **Deliverable**: Write `dev/research/transformation_analysis_paper.md`.
