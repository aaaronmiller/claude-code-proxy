---
title: Unified PRD — Open Gemini Deep Research (Full‑Stack + Chrome Extension) — WHAT and WHY
date: 2025-09-18 05:30:00 PDT
ver: 1.0.0
author: lil' Gimpy
model: Perplexity-AI
tags: [prd, deep-research, gemini, chrome-extension, obsidian, playwright, svelte, hono, bun]
---
# Deeper research - PRD — Open Gemini Deep Research
ee# Deeper research - PRD — Open Gemini Deep Research

A unified, comprehensive PRD is compiled below that consolidates all versions and related docs without condensing, preserving every requirement, selector, workflow, and rationale across the provided materials and the base upstream repository scope.[1][2]

This PRD focuses on the WHAT and the WHY of how the project operates, covering features, architecture, research modes, DOM automation, Chrome extension integration, Obsidian flows, technology choices, risks, and deliverables drawn from the documents and source references.[2][1]

### Vision and goals (WHY)
- The project delivers a powerful, locally-run, user-configurable automation platform for AI-driven research and data processing, enabling power users to visually build, modify, and chain complex workflows that interact with live web pages and large language models using transparent, extensible logic under full user control.[1]
- The immediate product goal is to create a robust, extensible research assistant that leverages Gemini’s Deep Research and Canvas web interfaces through browser automation, supports batch and hybrid research workflows, and integrates natively with Obsidian and a YouTube transcript pipeline to produce high-fidelity, auditable outputs.[1]

### Repository context and starting points (WHY/WHAT)
- Upstream baseline: Open Gemini Deep Research by eRuaro provides a Python-based deep research agent with defined modes, concurrency, progress tracking, and a research tree, forming the core functionality to extend via UI, DOM automation, and integrations.[2]
- The working fork is at aaaronmiller/open-gemini-deep-research, and this PRD references it as the target for new features and branch work, preserving and extending features while adding UI, automation, and integrations specified herein.[1]

### Problem framing and tech choice rationale (WHY)
- Historical front-end guidance referenced Create React App, but CRA deprecation and incompatibilities make it unreliable, thus the PRD adopts modern alternatives like Vite, Next.js, or SvelteKit, aligning with the user’s preferred stack and ecosystem for performance and dev experience.[3]
- The WHY: selecting Svelte/Hono/Bun or Next.js/shadcn avoids CRA failures and accelerates delivery while supporting better bundling, DX, and dark-mode UI consistency, directly addressing the issues documented with CRA and modern React 19 incompatibilities.[3]

***

### Core features (WHAT)
- Modern Web UI: A Next.js and shadcn/ui front end for a user-friendly interface to orchestrate all research tasks, with explicit toggles for research modes, batch operations, and workflow selection in dark mode as preferred, with extensibility for new agent endpoints and prompts.[1]
- Browser-Automated Research: Playwright-powered control of Gemini’s Canvas and Deep Research UIs, including mode selection, input entry, file attach, “Start research,” and copy/export behaviors under resilient selectors with retries and pacing.[1]
- Multi-Workflow Support: Deep Research with fast/balanced/comprehensive modes and a YouTube Transcript Analysis pathway that fetches transcripts and uses structured prompts to generate comprehensive analyses and downstream research inputs.[1]
- Obsidian Integration: All research reports and chat captures are saved to an Obsidian vault as Markdown with YAML frontmatter, including tags, traceability, and file mover automation for seamless archival and retrieval.[4][1]
- AI Chat Exporter: A Chrome extension captures chat logs across multiple AI sites (Gemini, ChatGPT, Claude, Perplexity, Grok, Kimi, DeepSeek, Ernie) into clean Markdown with enriched YAML and metadata for downstream vault processing.[4]

### Research modes and process (WHAT)
- Fast Mode: Quick surface scan with up to 3 concurrent queries, no recursion, typical 2–3 follow-ups per query, 1–3 minutes for time-sensitive queries and initial exploration.[2][1]
- Balanced Mode: Default moderate depth/breadth with up to 7 concurrent queries, 3–5 follow-ups per query, 3–6 minutes, exploring main concepts and immediate relationships.[2][1]
- Comprehensive Mode: Exhaustive deep research with recursive sub-queries, 5–7 follow-ups, exploring primary, secondary, tertiary relationships, including counter-arguments, 5–12 minutes.[2][1]
- End-to-end flow includes query analysis, semantic de-duplication of generated queries, a research tree with UUIDs, recursive exploration, progress tracking, and 3000+ word report generation with inline citations and structured synthesis.[2][1]

### Architecture overview (WHAT)
- Backend (Python + FastAPI): Central “brain” orchestrating workflow definitions, execution, automation calls, and persistence, featuring a workflow engine, Playwright browser controller, and RESTful endpoints for CRUD and run control.[1]
- Frontend (UI Shell): Initially described as React/CRA/Tailwind SPA with dashboard, workflow editor, and status monitor, but practically moving to Next.js/shadcn or SvelteKit with dark mode to avoid CRA pitfalls while retaining all planned UI affordances.[3][1]
- Capture Tools: Chrome extension and a Node.js background daemon (chokidar) watch for captured chat files and move them into the Obsidian vault with notifications and conflict-safe file handling.[4][1]

### Workflow engine concepts (WHAT)
- Workflows and Nodes: Users define nodes with DOM selectors, prompts, and logic, chaining them into reusable workflows with explicit data flow and saved configurations for repeatability and sharing across tasks.[1]
- Data Flow and Orchestration: The engine passes intermediate artifacts and context between nodes with logging, retry logic, versioning, and YAML/Markdown outputs to ensure full traceability during complex, multi-stage research runs.[1]

### UI/UX requirements (WHAT)
- Dashboard and Editor: List saved workflows, edit nodes, set selectors and prompts, visualize chains, initiate runs, and view real-time status with queued jobs and progress bars for batch/bulk use cases in a minimal, dark-mode UI.[1]
- Visualization: Research tree/state visualization JSON with collapsible views and job/phase tags to reflect parent-child relationships, completion, and learnings as part of the progress monitor and artifact audit.[1]

***

### DOM automation and selectors (WHAT)
- Canvas and Deep Research: Mode selectors include label detection for “Canvas” and “Deep Research,” input areas are contenteditable fields, and actions cover add files, send/submit, “Start research,” copy, and share for downstream export.[1]
- Selector map (high level):  
  - Prompt input: [contenteditable='true'][1]
  - Canvas label: div.label:has-text("Canvas")[1]
  - Deep Research label: div.label:has-text("Deep Research")[1]
  - Add Files: mat-icon[fonticon="add_2"][1]
  - Submit: mat-icon[fonticon="send"][1]
  - Start research: span.mdc-button__label:has-text("Start research")[1]
  - Copy output: span.mat-mdc-list-item-title:has-text("Copy")[1]
  - Share: mat-icon[data-test-id="share-icon"][1]
- YT transcript copy selector: span#copy-span on youtubetotranscript.com/transcript for pipeline integration and bulk operations.[1]

### Chrome extension capture (WHAT)
- Providers and selectors: Robust mapping across platforms to locate the main conversation container and fallback gracefully to body, supporting OpenAI, Perplexity, Claude, Gemini, Grok, Kimi, DeepSeek, and Ernie, with a default generic selector set.[4]
- Content extraction: Converts HTML to Markdown with code block cleanup, heading normalization, list conversion, and removal of residual tags, then packages enriched YAML frontmatter and extraction metadata for file save.[4]
- Background script: Ensures content script injection, sends capture message, retries with direct execution fallback, and downloads the capture file deterministically to support the mover daemon flow without prompts.[4]

### Obsidian integration and mover daemon (WHAT)
- Vault path and YAML: Reports and captures are saved as Markdown with YAML frontmatter tailored for Obsidian parsing, including title, summary, sources, username, generator/version, and trace tags for robust auditing.[4][1]
- ai-vault-mover.js: A chokidar-based Node daemon watches Downloads and subfolders for ai-session-*.md patterns, deconflicts names, moves to configured vault path, cleans empty directories, logs activity, and posts OS notifications on macOS/Linux.[4]
- Launcher script: A bash launcher manages dependencies via bun/pnpm/yarn/npm, forks to background with nohup, monitors PID/logs, and provides start/stop/status/restart commands with safety checks and notifications for reliability.[4]

***

### Output, logs, and artifacts (WHAT)
- Markdown + YAML: All outputs include consistent YAML frontmatter with query tags, versioning, and timestamping, plus optional attachment of HTML sources or sidecar files for deep provenance and reproducibility.[1]
- Research tree: The complete tree structure is dumped to research_tree.json at finalization to support later analysis, visualization, and post-hoc QA reviews of the agent’s exploration path.[2][1]
- Persistent logging: Full query/result audit logs with retries, error captures, version history, and batch/job tagging to support investigation, regression tests, and reproducible runs under evolving UI selectors.[1]

### Hybrid API + browser strategy and alternatives (WHAT/WHY)
- Hybrid approach: Prefer browser automation for Canvas/Deep Research to maximize context and artifact handling while permitting hybrid API calls when appropriate for speed or reliability, as explicitly recommended by the PRD context.[1]
- Perplexity variant: Provide an alternative deep research path powered by Perplexity as an option in the UI, maintaining selector/config modularity so switching providers is a slot-in operation for experimentation and parity testing.[1]

### YouTube transcript pipeline (WHAT)
- Transcript analysis: Integrate a transcript-first flow that extracts the video’s workable structures, workflows, patterns, prompts, and principles, producing article-quality synthesis with appendices and genre-aware visuals when needed.[1]
- Downstream coupling: After transcript analysis, generate questions from extracted workflows and pass them into deep research to develop a more comprehensive, linked analysis that unifies both pipelines in single- and double-path options.[1]

***

### Non-functional requirements (WHAT/WHY)
- Reliability and resilience: DOM selectors are configurable in one place, with a test phase and retries to handle Gemini UI changes and localization, pinned browser and dependency versions in devcontainer/Docker for determinism, and strict logging.[1]
- Performance and scalability: Concurrency tuned per mode, queueing to enforce limits (e.g., 3 at a time for Deep Research), and pacing between batch jobs to avoid rate limits with recovery and failover strategies.[1]
- Security and secrets: Secrets reside in .env or injected configs, honoring do-not-touch guarantees and secret preservation rules, while keeping the whole process local and observable for power-user transparency.[1]

### Configuration and environment (WHAT)
- Execution environment: Local macOS with Playwright and Python, Chrome/Chromium available, VS Code/devcontainer supported, and user notifications via osascript or notify-send integrated into each pipeline stage.[1]
- Obsidian vault specifics: Store outputs in the configured vault path and ensure YAML parsing semantics align with installed Obsidian plugins, with username and generator/version fields set per PRD guidance.[1]

### Deliverables and success criteria (WHAT)
- UI deliverable: Clean, documented HTML/JS front end (Next.js/shadcn or SvelteKit) with dark mode, batch controls, mode toggles, selectors mapping, job queue views, and export/download actions surfaced prominently.[1]
- Automation deliverable: Playwright/Puppeteer scripts with docstrings for each selector and artifact stage, research tree maintenance, YAML/Markdown outputs, and robust logs with retry/versioning semantics.[1]
- Integration deliverable: Obsidian-ready files, Chrome extension compatibility for YouTube transcript and notification flows, and minimal deployment docs for Docker/devcontainer/bash to accelerate adoption.[1]

***

### Risks and open questions (WHY)
- UI drift risk: Gemini DOM changes can break selectors; mitigations include centralized selector config, selector tests, and rapid update processes with pinned browser/deps in containerized environments.[1]
- Rate limits and batch caps: Heavy parallel runs and long sessions may stress Deep Research and Canvas; queueing, retries, and graceful backoff are required to sustain large batches and meet user SLAs.[1]

### Competitive landscape and patterns (WHY)
- The PRD positions against general automation platforms like Zapier/n8n by emphasizing local transparency, visual workflow editing, DOM-first control, and reusability, targeting power users who need full-fidelity customization.[1]
- Broader OSS patterns show “open deep research” implementations using configurable agents, structured outputs, and hybrid search/LLM stacks, reinforcing the project’s emphasis on modularity and provider-agnostic design.[5][6]

### Safety notes for OS interactions (WHY)
- The mover and launcher scripts write to /tmp logs, fork to background, and issue notifications; guardrails include PID checks, stale-PID cleanup, dependency verification, and bounded runtime auto-restart to avoid orphan processes or log bloat.[4]
- Negative interactions to consider include incorrect VAULT_PATH causing exit, missing package managers, permission issues in Downloads, or killing unrelated PIDs; scripts explicitly check for these and provide actionable error messages and notifications.[4]

***

### Upstream baseline details to inherit (WHAT)
- Mode definitions, research process, concurrency characteristics, research tree semantics, and reporting guarantees (e.g., 3000+ word minimum, citations) are part of the baseline to preserve during feature expansion and UI integration.[2]
- Setup paths include Python 3.9+, .env with GEMINI_KEY, optional devcontainer, and CLI usage with mode, num-queries, and optional learnings parameters, which remain available beneath the UI layer and automation flows.[2]

### Required selectors and user-specific config (WHAT)
- Centralize selectors and user config: one Python/config file mapping all DOM entries, output labeling, and Obsidian YAML templating as a Jinja2 block, ensuring rapid updates when UI or localization shifts occur.[1]
- Maintain job tags, UUIDs, batch identifiers, and timestamps in all buffers and final artifacts so errors can be traced back to specific UI-origin labels or selector actions in the wrapper.[1]

### Prompts and structured analysis directives (WHAT)
- The transcript-analysis “gem” specifies a multi-phase analysis protocol with Mermaid mind map first, canonical definitions, algorithmic descriptions, pattern benefit tagging, prompt cataloging, QA gates, and benchmarking, which should be honored in the transcript mode.[1]
- The deliverable specification for transcript analysis includes executive summary, topic-based body sections, appendices for verbatim and constructed prompts, an evaluation checklist, and a benchmark rubric to ensure consistent evaluability.[1]

***

### Implementation notes and tactics (WHAT)
- UI tech: Prefer Next.js/shadcn or SvelteKit with dark mode to present mode toggles, batch input, live status, export buttons, and selector mapping panels, while minimizing bespoke CSS to reduce surface area for visual regressions.[3][1]
- Automation: Implement Playwright scripts with resilient waits and verification for mode selection, input, start actions, and copy/share paths, with per-action logging, retry policy, and optional snapshots for error triage in headless runs.[1]
- Storage: Persist research_tree.json per run, maintain a structured logs directory with job IDs, and write final Markdown to the configured Obsidian path with YAML including title, ai_summary, ai_sources, username, and generator/version.[1]

### Future work (WHAT)
- Drag-and-drop workflow builder, direct page content parsing nodes, community workflow library exchange, RBAC and user switching for long-running jobs, and scheduled triggers compatible with tools like n8n/Zapier/cron are identified future directions.[1]
- Plugin slots for non-text artifacts and multi-provider agent lists should evolve to cover image/table/zipped outputs and additional endpoints while preserving a stable front-end toggle and selector configuration panel.[1]

***

### Acceptance criteria (WHY)
- The system must run end-to-end with UI-driven research runs, DOM-automated Gemini sessions, robust logs, research tree persistence, Obsidian file outputs, and Chrome extension capture feeding the vault mover in background without manual intervention.[4][1]
- Batch runs in all modes must complete with consistent YAML frontmatter and job/batch tags, and the transcript pipeline must be able to generate downstream questions and pass them into deep research for deeper linked analyses.[1]

### Out-of-scope clarifications (WHY)
- The PRD does not require cloud-hosted, multi-tenant deployment or closed-source integration bundles, instead prioritizing local control, transparency, and modular addition of endpoints as user-configured “slots” for experimentation.[1]
- While UI initially referenced CRA, the PRD explicitly moves to modern stacks to avoid known failures, keeping the front-end minimal but extensible and aligned with the broader goals of power-user transparency and rapid iteration.[3]

***

### References and grounding (WHY)
- Upstream README and “How It Works” content establish definitions for modes, processes, and output guarantees that this PRD preserves as the core behavioral contract of the system.[2]
- This PRD consolidates project-specific PRD text, DOM selector maps, transcript protocol directives, Obsidian integration, Chrome extension code, and mover/launcher scripts from the provided documents without excluding content.[4][1]




PLAN:

---

title: Workflow and data extraction inventory — Open Gemini Deep Research  
date: 2025-09-18 05:42:00 PDT  
ver: 1.0.0  
author: lil' Gimpy  
model: Perplexity-AI  
tags: [workflows, data-extraction, gemini, chrome-extension, obsidian, playwright, automation, yaml]

---

Here is a complete inventory of workflows, selectors, prompts, configs, file conventions, and other concrete elements extracted from the provided attachments to use directly when generating the implementation plan later.chrome_extension_docs.md+1  
This is collection-only, not a plan or condensation, and it preserves all actionable components, structures, and parameters for the project’s next steps.PRD.md+1

## Workflows

- Deep Research engine with three modes that define breadth/depth and concurrency: Fast, Balanced, Comprehensive, including recursion and counter-arguments in the comprehensive path.PRD.md
    
- Research process pipeline: query analysis, unique query generation with semantic de-duplication, research tree building with UUIDs, recursive deep research (breadth reduction at depth), and minimum 3000-word report synthesis with citations.PRD.md
    
- Browser-automated Gemini flows for Canvas and Deep Research: mode selection, prompt entry, optional file attach, submit/send, delayed “Start research,” copy/share extraction, and downstream export.PRD.md
    
- YouTube transcript analysis flow: fetch transcript via a transcript tool pathway, run the advanced “Gemini Gem” transcript-analysis prompt, then optionally pass generated questions into deep research for a linked analysis (single-path and dual-path variants).PRD.md
    
- Chrome extension capture workflow: inject content script, detect provider, find conversation container with a selector map, extract HTML, convert to Markdown, generate YAML frontmatter, download to Downloads for the mover daemon to process.chrome_extension_docs.md
    
- Obsidian mover daemon flow: watch Downloads and subfolders for ai-session-*.md files, move with deconflict naming into the configured vault path, send OS notifications, and clean up empty directories; auto-restart after max runtime.chrome_extension_docs.md
    
- UI-centric workflow CRUD and run execution: dashboard for listing workflows, editor for node configuration (selectors, prompts), and status monitor for progress, errors, and live job tracing.PRD.md
    
- Hybrid research options and provider slotting: keep browser-automation for Gemini front-and-center while enabling alternate deep research via Perplexity and a final summarization model choice, with prompts and selectors stored as configurable assets.PRD.md
    
- Batch/queue discipline: enforce at-most-three parallel Deep Research tasks, queue remainder, add sleeps between jobs, and preserve error/retry logs with batch and UUID tagging in all artifacts.PRD.md
    

## Research mode parameters

- Fast: up to 3 concurrent queries, no recursion, typically 2–3 follow-ups per query, ~1–3 minutes targeted latency.PRD.md
    
- Balanced: up to 7 concurrent queries, no recursion, 3–5 follow-ups per query, ~3–6 minutes and default recommendation.PRD.md
    
- Comprehensive: 5 initial queries with recursive deepening, 5–7 follow-ups, exploring primary/secondary/tertiary relationships and counter-arguments, ~5–12 minutes.PRD.md
    

## Research tree and persistence

- Data structure: ResearchProgress with unique IDs per query, parent-child relationships, status, depth, and “learnings” aggregation per node.PRD.md
    
- Artifact: entire tree saved to research_tree.json during final report generation for later visualization and audit.PRD.md
    

## DOM automation selectors (Gemini/Canvas/Deep Research/YTT)

- Gemini prompt input: [contenteditable='true'].PRD.md
    
- Canvas mode selector: div.label:has-text("Canvas").PRD.md
    
- Deep Research selector: div.label:has-text("Deep Research").PRD.md
    
- Add files: mat-icon[fonticon="add_2"].PRD.md
    
- Submit/send: mat-icon[fonticon="send"].PRD.md
    
- Start research: span.mdc-button__label:has-text("Start research").PRD.md
    
- Copy output: span.mat-mdc-list-item-title:has-text("Copy").PRD.md
    
- Share: mat-icon[data-test-id="share-icon"].PRD.md
    
- YTT transcript copy: span#copy-span on youtubetotranscript.com/transcript.PRD.md
    

## Chrome extension — providers and selectors

- Provider detection map by URL regex with per-site selector lists: OpenAI (chat.openai.com), Perplexity (perplexity.ai), Claude (claude.ai), Gemini (gemini.google.com), Grok (grok.x.ai), Kimi (kimi), DeepSeek (deepseek), Ernie (ernie), with a generic fallback to .main-chat-container, main, body.chrome_extension_docs.md
    
- Extraction routine: pick first selector that yields >50 chars of text, otherwise fallback to body; convert outerHTML to Markdown via an htmlToMarkdown function that normalizes pre/code, br, li, headings, paragraphs, and strips remaining tags.chrome_extension_docs.md
    
- Filename pattern: ai-session-${service}-${YYYY-MM-DDTHH-MM-SS}.md with colons replaced and millis removed for deterministic paths.chrome_extension_docs.md
    
- YAML frontmatter fields in export: date, provider, session_url, chat_selector, extraction_time, word_count, char_count, followed by “Extraction Metadata” section listing Provider, URL, Selector Used, Captured, and Content Length.chrome_extension_docs.md
    
- Messaging and download: background injects content.js, sends “extract_ai_chat”, falls back to executeScript if messaging fails, then downloads Blob via chrome.downloads with saveAs=false and conflictAction='uniquify'.chrome_extension_docs.md
    

## Obsidian mover daemon and launcher

- package.json: ai-vault-mover with chokidar dependency and scripts start/daemon to run ai-vault-mover.js.chrome_extension_docs.md
    
- ai-vault-mover.js configuration: APP_NAME, DOWNLOADS_DIR (~/Downloads), VAULT_PATH (Documents/ChetasVault/ai_transcripts — update path), FILE_PATTERN /^ai-session-.*.md$/, CHECK_INTERVAL seconds, MAX_RUNTIME_HOURS auto-restart, LOG_FILE /tmp/${APP_NAME}.log, PID_FILE /tmp/${APP_NAME}.pid.chrome_extension_docs.md
    
- Watch paths: Downloads, Downloads/ChetasVault, Downloads/ai-chats; ignore dotfiles; depth 2; awaitWriteFinish enabled; on add matching pattern, delay 500ms, move file with unique naming if conflict and notify success/failure.chrome_extension_docs.md
    
- PID handling and single-instance guard: checkIfRunning uses PID file and kill -0; removes stale PID; ensures VAULT_PATH exists with fatal exit if missing; writes PID and registers signal/exception handlers.chrome_extension_docs.md
    
- Notifications: osascript on macOS or notify-send on Linux for start, move events, errors, and auto-restart messages.chrome_extension_docs.md
    
- Background mode behavior: forks when launched in GUI contexts to run as BACKGROUND_MODE using child_process spawn and unref.chrome_extension_docs.md
    
- ai_vault_launcher.sh: start/stop/status/restart controls, PID/log paths in /tmp, dependency installer choosing bun/pnpm/yarn/npm, nohup launch to background, wait-for-daemon with MAX_STARTUP_WAIT, and notify integration.chrome_extension_docs.md
    

## Outputs and YAML conventions

- Research reports: Markdown with YAML frontmatter including title, ai_summary, ai_sources, username, generator/version, tags, and batch/UUID associations where applicable for provenance and audit.PRD.md
    
- Minimum report characteristics: coherent narrative of at least 3000 words with inline citations, organized by relevance/relationship, optionally adding scenarios and analogies while maintaining factual accuracy.PRD.md
    
- Tree/state artifacts: research_tree.json stored at finalization to enable retrospective visualization and QA of traversal and learnings aggregation.PRD.md
    

## Configuration, environment, and secrets

- Runtime environment: Local macOS with Python 3.9+, Playwright-controlled Chrome/Chromium, and VS Code/devcontainer or Docker-based setup for determinism and portability.PRD.md
    
- Obsidian vault configuration: target path noted as ~/documents/ChetaValut in PRD context and Documents/ChetasVault/ai_transcripts in mover script, which should be reconciled during configuration.PRD.md
    
- Secrets and API keys: Gemini API key injected into .env or secrets store; variable name GEMINI_API_KEY referenced for default conventions and simplicity.PRD.md
    

## Scheduling, queueing, and batch constraints

- Queue discipline: cap Deep Research to three concurrent automations, queue remainder, and insert sleeps between batch jobs to mitigate rate/batch caps with retry/failover.PRD.md
    
- Delay/scheduling requests: ability to schedule injections over time windows (e.g., every N hours), including reading queued tasks from a Downloads/to-do folder to trigger configured workflows.PRD.md
    

## UI components and behaviors

- Dashboard: list/manage saved workflows with mode toggles, batch inputs, and quick actions for Start, Pause, Cancel, Export, Download artifacts, and version/license/footer references.PRD.md
    
- Workflow Editor: form-based node builder where users define selectors, prompts, and chaining, with visualization of data flow and storage of reusable configurations.PRD.md
    
- Status Monitor: real-time progress with job tags, phases, queue state, error/retry messages, and JSON research tree visualization for traceability.PRD.md
    

## Prompts, templates, and analysis directives

- Gemini “Gem” for transcript_analysis_and_extraction: a structured XML system prompt specifying goals, quality standards, output formatting, research methodology, a seven-phase analysis protocol, content analysis requirements, deliverable specification, and input data append section for transcripts.PRD.md
    
- Key elements include a mandatory Phase 1 Mermaid mind map, canonical definitions, algorithmic/state-machine descriptions, pattern benefit tagging, prompt cataloging with verbatim/synthesized splits, methodological defense, evaluation checklist, benchmark rubric, and article assembly with meta-learning.PRD.md
    
- Additional enforcement directives: always include Obsidian-style header block, maintain secret preservation, escape spaces in Bash, prefer macOS defaults, and analyze other approaches and OS interaction risks when doing research or command design.PRD.md
    

## Provider and endpoint slotting concepts

- Endpoints taxonomy: AI research endpoints, consolidation endpoints, task-determination endpoints, website-bounce endpoint (e.g., YouTube transcript tool), with interchangeable DOM definitions for textarea/input/submit/attach and optional deep research “start” control.PRD.md
    
- Extensibility: name and save endpoint definitions, support add/edit/delete/testing in UI, and enable branching/recursion and multi-model bouncing using configured endpoints.PRD.md
    

## Hybrid and alternate research paths

- Hybrid approach: browser-first (Gemini Canvas/Deep Research) with optional API usage for speed or reliability, while keeping artifact handling and large context benefits of DOM automation.PRD.md
    
- Perplexity alternative: define workflows to use Perplexity for deep research, or run Gemini and Perplexity in parallel and summarize best answers, with a selectable final model for summarization and prompt modularity.PRD.md
    

## File, naming, and directory conventions

- Chrome capture files: ai-session-${service}-${ISO-with-dashes}.md landing in Downloads, then moved to vault with unique naming if conflicts present.chrome_extension_docs.md
    
- Logs and PIDs: /tmp/ai-vault-mover.log and /tmp/ai-vault-mover.pid with a separate /tmp/${APP_NAME}-daemon.log for launcher-driven nohup outputs.chrome_extension_docs.md
    
- Watch roots: ~/Downloads plus common subfolders like ChetasVault or ai-chats, with configurable depth and awaitWriteFinish settings.chrome_extension_docs.md
    

## Error handling, retries, and notifications

- Research engine: retry logic, progress tracking, error capture with per-query/tag versioning, and full audit logs for reproducibility and regression testing.PRD.md
    
- Extension/mover: content script injection fallback, direct executeScript extraction if messaging fails, move failures reported via OS notifications, and daemon auto-restart after configured runtime.chrome_extension_docs.md
    

## Known mismatches and to-reconcile items

- Obsidian vault path mismatch: PRD references ~/documents/ChetaValut while mover uses Documents/ChetasVault/ai_transcripts; a single canonical path should be selected for consistent behavior.PRD.md
    
- UI tech references: PRD mentions a React/CRA/Tailwind SPA and a Next.js/shadcn UI; consolidation into a single modern stack is expected during planning while retaining all controls/toggles.PRD.md
    

## Direct artifacts to include in repo (verbatim sources)

- Selectors registry: the Gemini/Canvas/Deep Research/YTT selector list provided above should be placed into a central config artifact for quick updates and localization handling.PRD.md
    
- Extension sources: content.js, background.js logic, and htmlToMarkdown transform behavior are concrete, production-ready starting points for capture integration with Obsidian mover.chrome_extension_docs.md
    
- Mover/launcher: ai-vault-mover.js with its configs, watch paths, move/deconflict logic, and ai_vault_launcher.sh control script are ready to be included with only VAULT_PATH reconciliation required.chrome_extension_docs.md
    

## Data points for plan inputs

- Mode caps and timings, recursion rules, and breadth scaling at depth for comprehensive mode.PRD.md
    
- Required outputs: minimum 3000-word reports, research_tree.json, and Markdown/YAML with frontmatter fields including username and generator/version.PRD.md
    
- Message flows and file patterns: extension messaging, download options, file naming regexes, and mover pattern matching.chrome_extension_docs.md
    
- OS interactions: notify via osascript/notify-send, PID safety, stale PID cleanup, and fork-to-background for daemonization.chrome_extension_docs.md
    
- Security/secrets: GEMINI_API_KEY in .env or secrets file and secret preservation directives in prompt standards.PRD.md
    

Lil’ Gimpy has extracted these concrete components so they can be directly slotted into an implementation plan without additional parsing, keeping all selectors, file patterns, prompts, flows, and constraints intact for the upcoming build phase.chrome_extension_docs.md+1

1. [https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/1fc85183-a6a8-4f13-a0b3-1f8e274e4a5a/chrome_extension_docs.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/1fc85183-a6a8-4f13-a0b3-1f8e274e4a5a/chrome_extension_docs.md)
2. [https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/3cdacbff-60e3-4f15-af76-10de5c002b1c/PRD.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9737283/3cdacbff-60e3-4f15-af76-10de5c002b1c/PRD.md)