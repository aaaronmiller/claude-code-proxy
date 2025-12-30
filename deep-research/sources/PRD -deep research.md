# PRD -deep research

This project is a powerful, full-stack research assistant that uses a web UI to orchestrate deep, multi-layered research on any topic. It leverages browser automation to interact with Google's Gemini for its research capabilities and includes a suite of tools for capturing and organizing information.

## Core Features

- **Modern Web UI**: A Next.js and shadcn/ui frontend provides a user-friendly interface for all research tasks.
- **Browser-Automated Research**: Uses Playwright to automate interactions with Gemini, enabling deep research, canvas mode, and more without needing an API key.
- **Multiple Research Workflows**:
  - **Deep Research**: The core multi-step research engine.
  - **YouTube Transcript Analysis**: Fetches a YouTube transcript and uses an advanced prompt to perform a deep analysis.
- **Obsidian Integration**: All research reports and chat captures are saved directly to your Obsidian vault in a clean, Markdown format with YAML frontmatter.
- **AI Chat Exporter (Chrome Extension)**: A companion browser extension to capture chat logs from various AI platforms (Gemini, ChatGPT, Claude, etc.) and save them to your vault.


Product Requirements Document:
A Dynamic, User-Configurable AI Workflow Automation Platform
1. Vision & Goals
The Janus project aims to create a powerful, locally-run, and fully user-configurable automation platform for AI-driven research and data processing. Where commercial tools like Zapier offer user-friendly but often restrictive, cloud-based solutions, Janus provides a transparent, extensible, and power-user-focused alternative.

The core vision is to empower users to visually build, modify, and chain complex automation workflows that interact with live web pages and large language models. By giving users direct control over the DOM selectors, prompts, and logic of their automation "nodes," Janus will enable a level of customization and adaptability that is impossible to achieve with closed-source platforms. It is a tool for users who want to build their own "personal Enigma machine" for information processing, without paying for a service or being limited by a predefined set of integrations.

Primary Goals:

Empowerment: Give users full control over the automation logic.
Extensibility: Allow users to define their own "endpoints" for any website or AI model.
Transparency: Keep the entire process local and observable.
Reusability: Enable users to save, share, and re-use complex workflow configurations.
2. System Architecture
The Janus platform is composed of three primary components that work in concert. This architecture is designed for modularity and clear separation of concerns.

1. Backend (Python & FastAPI):

Role: The "brain" of the application. It is responsible for storing and managing workflow definitions, executing the automation tasks, and exposing a comprehensive API for the frontend to consume.
Technology: Built with Python 3.9+ and the FastAPI web framework for high performance.
Key Sub-components:
Workflow Engine: Orchestrates the execution of saved workflows, passing data between nodes.
Browser Controller: A service built on Playwright that handles all direct browser interactions (navigating, clicking, typing, scraping).
API Endpoints: A set of RESTful endpoints for CRUD operations on workflows and for initiating workflow runs.
2. Frontend (React & Create React App):

Role: The "face" of the application. The frontend provides the entire user experience, allowing users to build, manage, and run their automation workflows.
Technology: A modern single-page application (SPA) built with React 18, Create React App, and Tailwind CSS for styling.
Key Sub-components:
Dashboard: The main view for listing and managing all saved workflows.
Workflow Editor: A form-based UI where users can define new automation nodes, configure their parameters (selectors, prompts), and chain them together into a workflow.
Status Monitor: A component that communicates with the backend API to provide real-time feedback on running workflows.
3. Capture Tools (Chrome Extension & File Mover):

Role: An optional but powerful set of tools for capturing data from the web to be used as inputs for workflows or for simple archival.
Technology: A standard Chrome browser extension (javascript) and a Node.js background daemon (chokidar).
Functionality: The extension scrapes chat logs from various AI websites, saves them as Markdown files, and the file mover daemon automatically organizes these files into the user's Obsidian vault.
3. Core Components: The Workflow Engine
A detailed look at the core concepts of "Workflows" and "Nodes".

3.1. Workflows
3.2. Nodes
3.3. Data Flow
4. Feature Details
A breakdown of all the specific features the platform will have.

4.1. Workflow CRUD (Create, Read, Update, Delete)
4.2. Workflow Execution Engine
4.3. Scheduling & Event-Based Triggers
4.4. Import & Export
4.5. Hybrid & Parallel Execution
4.6. Meta-Programming via YAML
5. UI/UX Vision
A textual description of the user interface and user experience.

5.1. Main Dashboard
5.2. The Workflow Editor
5.3. Workflow Visualization
6. Competitive Analysis
An analysis of how Janus compares to existing platforms like Zapier, n8n, etc.

6.1. Key Differentiators
6.2. Market Positioning
7. Future Work
A list of potential features and improvements for future versions.

7.1. Codeless Drag-and-Drop Interface
7.2. Direct Page Content Parsing
7.3. Community Workflow Librar

HOW IT WORKS

Research Modes
The application offers three research modes that affect how deeply and broadly the research is conducted:

Fast Mode

Performs quick, surface-level research
Maximum of 3 concurrent queries
No recursive deep diving
Typically generates 2-3 follow-up questions per query
Best for time-sensitive queries or initial exploration
Processing time: ~1-3 minutes
Balanced Mode (Default)

Provides moderate depth and breadth
Maximum of 7 concurrent queries
No recursive deep diving
Generates 3-5 follow-up questions per query
Explores main concepts and their immediate relationships
Processing time: ~3-6 minutes
Recommended for most research needs
Comprehensive Mode

Conducts exhaustive, in-depth research
Maximum of 5 initial queries, but includes recursive deep diving
Each query can spawn sub-queries that go deeper into the topic
Generates 5-7 follow-up questions with recursive exploration
Explores primary, secondary, and tertiary relationships
Includes counter-arguments and alternative viewpoints
Processing time: ~5-12 minutes
Best for academic or detailed analysis
Research Process
Query Analysis

Analyzes initial query to determine optimal research parameters
Assigns breadth (1-10 scale) and depth (1-5 scale) values
Adjusts parameters based on query complexity and chosen mode
Query Generation

Creates unique, non-overlapping search queries
Uses semantic similarity checking to avoid redundant queries
Maintains query history to prevent duplicates
Adapts number of queries based on mode settings
Research Tree Building

Implements a tree structure to track research progress
Each query gets a unique UUID for tracking
Maintains parent-child relationships between queries
Tracks query order and completion status
Provides detailed progress visualization through JSON tree structure
Deep Research (Comprehensive Mode)

Implements recursive research strategy
Each query can generate one follow-up query
Reduces breadth at deeper levels (breadth/2)
Maintains visited URLs to avoid duplicates
Combines learnings from all levels
Report Generation

Synthesizes findings into a coherent narrative
Minimum 3000-word detailed report
Includes inline citations and source tracking
Organizes information by relevance and relationship
Adds creative elements like scenarios and analogies
Maintains factual accuracy while being engaging
Technical Implementation
Uses Google's Gemini AI for:
Query analysis and generation
Content processing and synthesis
Semantic similarity checking
Report generation
Implements concurrent processing for queries
Uses progress tracking system with tree visualization
Maintains research tree structure for relationship mapping
Research Tree Implementation
The research tree is implemented through the ResearchProgress class that tracks:

Query relationships (parent-child)
Query completion status
Learnings per query
Query order
Unique IDs for each query
The complete research tree structure is automatically saved to research_tree.json when generating the final report, allowing for later analysis or visualization of the research process.

Example tree structure:



{
  "query": "root query",
  "id": "uuid-1",
  "status": "completed",
  "depth": 2,
  "learnings": ["learning 1", "learning 2"],
  "sub_queries": [
    {
      "query": "sub-query 1",
      "id": "uuid-2",
      "status": "completed",
      "depth": 1,
      "learnings": ["learning 3"],
      "sub_queries": [],
      "parent_query": "root query"
    }
  ],
  "parent_query": null
}




here is your PRD, save it and refernce it as needed:
date: 2025-09-17 15:40:00 PDT ver: 1.0.0 author: lil-gimpy model: perplexity-llm-2025-09 tags: [prd, gemini, open-gemini-deep-research, html-wrapper, automation, browser-automation, multi-agent, obsidian, dom, workflow, ai]

Product Requirements Document (PRD):
Open Gemini Deep Research — HTML Wrapper and Agentic Automation
Repo: https://github.com/aaaronmiller/open-gemini-deep-research
For: Juules (primary dev implementer)

1. Project Goal
Create a robust, extensible research assistant (standalone and orchestrated) that leverages Gemini’s Deep Research and Canvas web interfaces, supports bulk and batch research workflows, and natively integrates with Obsidian vaults and YT-to-transcript flows.
This upgrade should add a modern HTML UI wrapper, new agentic workflow logic, browser DOM automation, persistent log/history, notifications, and extra artifact/export handling.

2. Key Features & Functional Requirements
A. User Interface (Frontend/HTML Shell)
Modern HTML/JS UI (Next.js, shadcn/ui, or basic Flask/React accepted)
Input box for queries & batch mode (list of YouTube URLs, research prompts, etc.)
Research mode/agent selection toggle (Canvas, Deep Research, Multi-agent, YouTube→Transcript)
Display queue/batch status: live query/phase, clear tracking per job/tag/version
Action buttons: Start, Pause, Cancel, Export, Download outputs/artifacts
Notifications:
On phase complete or error (desktop/os/JS)
Log extract/last status as in-app popup or banner
Version, license, and “Powered by Gemini, forked from eRuaro” footer
B. Research Pipeline Logic (Backend & Automation)
Incorporate/maintain core capabilities of original eRuaro pipeline:

Multi-step deep research (fast/balanced/comprehensive), concurrent queries (max 3 at once for Deep Research)
Branching research tree with UUID tagging, error recovery, and YAML/markdown output
Progress logging, retry logic, and full query/result audit log
Output in Markdown with prefilled YAML frontmatter (title, ai_summary, ai_sources, username, generator/version, etc.)
Research artifact buffer: store output for each query with tag for error tracking/versioning
DOM Automation for Gemini/Canvas:

Playwright/Puppeteer-backed browser robot using provided selectors:
Model and mode selectors (“Canvas”, “Deep Research”), Input selectors (contenteditable, textareas)
Submit, Add File, Start Research, and Copy result selectors
Obsidian artifact handoff via file or Obsidian URI
YT-transcript pathway via copy button selector
Pause/sleep between batch jobs; retry/failover for rate/batch caps
Notification (notify-send, osascript, or JS popover) for completion/error
YT-to-Transcript Path:

Chrome extension or headless Playwright integration for single/bulk URL conversion
Annotate/capture source and expected result per job, with error log if output absent
Extensibility/Modularity:

Robust config for all selectors
Pluggable agent list: add new AI endpoints or agents for future expansion
Plugin point or slot to support non-text artifacts (images, tables, zipped source), with placeholder UI/notes for when this is toggled on
C. Output Handling
Obsidian integration: Create/import .md in ~/documents/ChetaValut; ensure title, frontmatter, YAML parsing is honored by Obsidian plugins
Retain job/phase tags and query associations in artifact name or inside YAML (for trace/debug)
Option to “attach” all artifact HTML sources in YAML or as sidecar files
D. Operational & Non-Functional
Error logging and job versioning, both console and as persistent file store (JSON/MD)
User/passphrase and API key config for Gemini (as in repo .env)
Docker/devcontainer support maintained
Accessible/configurable to non-root Linux/macOS users (Python 3.9+, Chrome/Chromium)
3. Advanced/Optional Features
Research tree/state visualization (as JSON, collapsible in UI)
RBAC/user switching for long-running agentic jobs
Export/Import state and config as YAML, JSON, Markdown (for backup/restore)
Scheduled jobs/automation triggers (for n8n, Zapier, cron-based workflows)
4. Deliverables and Success Criteria
Clean, documented HTML (Next.js or Flask or React, minimal viable)
All agentic browser automation scripts, app as repo’s Python module or subdir, docstring for each selector and artifact stage
Maintained research tree and YAML/MD output tracked by query tag/version, with persistent log
Manual/README and minimal deployment guide (Docker/devcontainer/bash)
Chrome extension compatibility for YT-transcript and notification flow
5. Identified Risks / Open Questions
Ensure DOM selectors/pipelines are resilient to Gemini UI changes (add config/selector test phase)
Pin Chrome/Chromium and package versions in Docker/devcontainer for deterministic browser launches
Confirm rate-limits/batch caps for Deep Research and Canvas survive heavy task load or parallel runs (>100)
Optional: if non-text exports/artifacts are needed, develop “artifact handler” stub for future extension
Summary:
Deliver a robust, extensible, and tracked multi-agent Gemini Deep Research tool with a modern HTML UI, full batch/YT/Canvas/Obsidian flows, and notifications/logging.
Ready for full implementation by a senior Python/JS dev!

1

additional info:
date: 2025-09-17 15:42:00 PDT ver: 1.0.0 author: lil-gimpy model: perplexity-llm-2025-09 tags: [dom, selectors, user-info, gemini, configuration, html-ui, open-gemini-deep-research, integration, context]

All User-Specific DOM and Structural Information for open-gemini-deep-research Enhancement
A. DOM Selectors for Automation (Gemini/Deep Research/Canvas/YTT)
Gemini Generic Chat/Prompt Input:
[contenteditable='true']

Gemini Canvas Mode Selector:
div.label:has-text("Canvas")

Gemini Deep Research Selector:
div.label:has-text("Deep Research")

Gemini Add Files Button (attachment):
mat-icon[fonticon="add_2"]

Gemini Submit/Send Query:
mat-icon[fonticon="send"]

Gemini Start Research (after 15s):
span.mdc-button__label:has-text("Start research")

Gemini Copy to Clipboard (output):
span.mat-mdc-list-item-title:has-text("Copy")

Gemini Share Button (for copy/export):
mat-icon[data-test-id="share-icon"]

YTT Transcript “Copy” Button:
span#copy-span
(For youtubetotranscript.com/transcript)

B. User-Specific & System Information
Obsidian vault path:
~/documents/ChetaValut
Obsidian YAML username:
MacUser
**Gemini Canvas and Deep Research should be accessed via browser automation, not API, to maximize context windows and artifact handling.
Execution Environment:
Local macOS, root available, Playwright and Python
Chrome/Chromium and VSCode/devcontainer supported
Notification system:
Use osascript/notify-send or in-app JS popups
Response/Job Tagging:
Every copied output gets a tag (from selection button or artifact source, mapped in HTML wrapper/start page for reference/error/history)
Pause/Queue Management:
Workflow should respect 3-at-a-time limits for Deep Research, queue remaining, and handle delays
Start triggers:
YT→Transcript can trigger from Chrome extension or local HTML interface; bulk jobs from HTML input
Output and error versioning:
All agentic/canvas/Deep Research responses should be buffered with query UUID, batch, and timestamp
C. Not Yet in PRD (Additional Context)
Content.js/background.js/ai-vault-mover.js provided:
For Chrome extension integration, file move/watcher, and background artifact handling
HTML frontend to enable launch, query labeling, workflow selection:
Plan to use/extend fdarkaou/open-deep-research HTML wrapper if further UI required
Sample prompts and prompt templates:
(See earlier: 7-point Gemini instructions, YAML summary requests, etc.)
Research mode options:
Should honor fast / balanced / comprehensive pipeline parameters
D. To Get Started
Map all selectors and config values to a single Python/config file for easy scripting and selector upgrades
Generalize input for tag/UI-origin labeling for output files/artifacts
Initialize error logger and notification channel in every agentic step
Plumb Obsidian YAML generator/template as function or Jinja2 block for markdown output
If any DOM selector changes (UI update or localization), update the config and rerun Pip/Playwright install.
All major workflow and context needs are above—Juules can start with this as their selector/config “Rosetta Stone.”

use that and complete the project; let me know if there is addtional informationyou require. gemini API key will be injected at the end into .env or .secrets file your choice (also config to work based on global api key access, GEMINI_API_KEY (confirm name; i use default, this is even easier) GO GO GO ULTRA THINK MAX VERBOSITY oh guidlines for the HTML interface are to use node and shadCN , dark mode make it pretty !




be sure to add toggles and selectors to make all of the forked projects capabilites accessable via the html page. also add additional functinoality as you see fit (extra prompts, recursive structure defnintions, etc) maybe add a way to use a youtube transcription to then generate questinos based on the transcript ouitput to then pass to the deep research to develop a deeper analysis ? like you video describes a new program and how to use it, we get all the workflows from the yt trancription pathway and then feed to deep reserarch. here is the gemini gem text:

<prompt_system>  

 

      

      

    <task_type>transcript_analysis_and_extraction</task_type>  

 

  <core_objective>  

    <primary_task>  

      Summarize core concepts discussed in the video transcript, define all structures, patterns, workflows, and interconnected ideas with maximum fidelity and actionability.  

    </primary_task>  

      

    <success_criteria>  

      Extract actionable structures, workflows, patterns, prompts, and meta-principles from source material, producing article-quality synthesis with defensible methodology, genre-aware visualizations, and comprehensive appendices.  

    </success_criteria>  

  </core_objective>

  <critical_directives priority="essential">  

    <code_requirements>  

     

          

          

          

          

          

          

        <database_setup>turso, cloudflare-d1, neon-postgres, prisma-postgresql, mongodb-atlas, supabase</database_setup>  

          

        <package_managers>npm, pnpm, bun</package_managers>  

          

        

        

      <quality_standards>  

          

        <file_structure>Always output code as entire file, include error corrections and follow standards</file_structure>  

        <data_handling>Use superior data structures when available; only SECRETS and missing data can be simulated</data_handling>  

        <secret_preservation>If provided code contains secrets, they MUST remain intact unless expressly directed otherwise</secret_preservation>  

      </quality_standards>  

    </code_requirements>

    <output_formatting>  

      <obsidian_tags>Always include obsidian tagging at top: title, tags, links. Add 4-10 relevant tags, include #claude</obsidian_tags>  

      <code_comments>Comment all code output. Never use markdown tags inside markdown comments</code_comments>  

      <bash_escaping>Always escape spaces in BASH commands with backslashes</bash_escaping>  

      <platform_default>Code defaults to macOS unless specified</platform_default>  

    </output_formatting>

    <research_methodology>  

      <comprehensive_analysis>Include analysis of how others approach the question and their patterns</comprehensive_analysis>  

      <os_interaction_safety>For OS instructions, analyze potential negative interactions from commands</os_interaction_safety>  

    </research_methodology>

    <header_block>  

     

        ---  

        date: {{DATE}} {{TIME}} {{TZ}}  

        ver: {{VERSION}}  

        author: {{AUTHOR}}  

        model: {{MODEL}}  

        tags: {{TAGS}}  

        ---  

        

     

        <date_format>YYYY-MM-DD HH:MM:SS TZ</date_format>  

        <tags_format>4-10 lowercase, CSV, markdown-style tags in [ and ] brackets</tags_format>  

          

        

    </header_block>  

  </critical_directives>

  <analysis_protocol>  

    <phase_1 name="read_and_map">  

      <visual_concept_map>  

        Start by generating a visual concept map as the first artifact using Mermaid mind map syntax, and present it before any prose to provide an at-a-glance overview and surface non-linear connections early; use a single root and hierarchical branches for entities, relationships, constraints, and dependencies, in a fenced code block labeled "mermaid" starting with "mindmap".  

        Example scaffold:  

                mindmap           Root((Core Topic))             Entities               Entity A               Entity B             Relationships               A → B             Constraints               Constraint X             Dependencies               Dep 1          

      </visual_concept_map>  

      <concept_mapping>Build a concept graph of entities, relationships, constraints, and dependencies; mirror this structure in the Mermaid mind map and maintain semantic consistency into subsequent prose.</concept_mapping>  

      <genre_identification>Identify genres (research, coding, planning, policy, pedagogy) and subgenres</genre_identification>  

      <methodology_extraction>Note explicit methodologies, implicit heuristics, and failure/edge cases</methodology_extraction>  

    </phase_1>

    <phase_2 name="genre_specific_assembly">  

      <wrapper_selection>Select wrapper from method "pillars" library (continuous workflow, research-enhanced analysis, QA gates, meta-learning, citations)</wrapper_selection>  

      <methodology_justification>Explain chosen combination and how it addresses the text's task geometry</methodology_justification>  

    </phase_2>

    <phase_3 name="extraction_and_formalization">  

      <canonical_definitions>Produce canonical definitions for patterns, workflows, and frameworks</canonical_definitions>  

      <algorithmic_descriptions>Provide algorithmic descriptions and state machines for iterative processes</algorithmic_descriptions>  

      <visualization_strategy>Prefer prose, but when iteration/branching dominates, include Mermaid diagrams and justify inclusion</visualization_strategy>  

      <pattern_benefit_tagging>  

        For every extracted pattern, assign exactly one primary benefit tag from the allowed set and place it inline at the end of the pattern name or definition: [Reduces Friction], [Deepens Thinking], [Improves Context], [Accelerates Execution], [Enhances Reliability], [Improves Transferability].  

      </pattern_benefit_tagging>  

    </phase_3>

    <phase_4 name="prompt_cataloging">  

      <appendix_a>Verbatim prompts with exact quotation and provenance</appendix_a>  

      <appendix_b>Constructed prompts (clearly labeled as synthesized) with usage notes, input schemas, and expected outputs</appendix_b>  

      <prompt_tagging>Tag each prompt with genre, difficulty, and intended LLM capabilities</prompt_tagging>  

    </phase_4>

    <phase_5 name="methodological_defense">  

      <deviation_justification>When deviating from requested formats, defend the choice in 2-3 sentences citing clarity, fidelity, or evaluability</deviation_justification>  

      <gap_analysis>Surface contradictions or gaps; propose reconciliations or experiments</gap_analysis>  

    </phase_5>

    <phase_6 name="quality_evaluation">  

      <coverage_checklist>Include checklist of coverage (topics, methods, prompts, edge cases)</coverage_checklist>  

      <validation_framework>Provide test questions or tasks to validate each extracted construct</validation_framework>  

      <benchmark_rubric>  

         

      </benchmark_rubric>  

    </phase_6>

    <phase_7 name="output_assembly">  

      <article_structure>Deliver a structured article with sections and graceful prose</article_structure>  

      <meta_learning>Close with a meta-learning note: how to improve extraction next time</meta_learning>  

    </phase_7>  

  </analysis_protocol>

  <content_analysis_requirements>  

    <summary_approach>  

      <list_formatting>Use bulleted or numbered lists, or Mermaid diagrams depending on utility for explaining concepts</list_formatting>  

      <iteration_handling>If iteration is involved, use Mermaid diagrams</iteration_handling>  

      <alternative_methods>If a better method exists than described, use it and defend the decision</alternative_methods>  

      <phase_1_visual_requirement>Phase 1 must open with a Mermaid mind map to present big-picture relationships before prose and to detect cross-links early.</phase_1_visual_requirement>  

    </summary_approach>

    <llm_prompt_extraction>  

      <verbatim_identification>Identify specific LLM prompts described verbatim by speakers</verbatim_identification>  

      <conceptual_identification>Identify general concepts of prompts discussed</conceptual_identification>  

      <contextual_analysis>Provide a contextual paragraph about conversation context leading to prompt discussion</contextual_analysis>  

      <example_generation>For non-verbatim prompts, generate examples and clearly indicate construction vs verbatim</example_generation>  

    </llm_prompt_extraction>  

  </content_analysis_requirements>

 

      

    <citation_requirements>Cite sources explicitly when quoting or adopting claims</citation_requirements>  

      

    <pattern_benefit_enforcement>Ensure each extracted pattern includes exactly one primary benefit tag from the allowed set and appears consistently in summaries, bodies, and appendices.</pattern_benefit_enforcement>  

 

  <deliverable_specification>  

    <article_components>  

      <executive_summary/>  

      <body_sections topic_based="true"/>  

     

      <appendix_a description="verbatim prompts"/>  

      <appendix_b description="constructed prompts"/>  

      <evaluation_checklist/>  

      <benchmark_rubric/>  

    </article_components>  

  </deliverable_specification>

  <input_data>  

   

      {{TRANSCRIPT_CONTENT_WILL_BE_APPENDED_HERE}}  

      

  </input_data>  

</prompt_system>

for context. the other gemnini gem is https://gemini.google.com/gem/6f2c1a3e176f

and its context is: You excell in summaring the core concepts discussed in the video transcript below, and define all structures, patterns, workflows, and interconnected ideas as you able to.

Start by generating a visual "concept map" in Phase 1, using a tool like Mermaid's mind map feature. This will provide a clearer, at-a-glance overview of all entities and their relationships before beginning the prose-writing phase, potentially surfacing connections that might otherwise be missed during a linear read-through. Additionally, explicitly tag each extracted pattern with its primary benefit (e.g., [Reduces Friction], [Deepens Thinking], [Improves Context]) to make the final output even more scannable and actionable for the reader.

=IT IS ESSENTIAL THAT YOU ALWAYS FOLLOW THE FOLLOWING DIRECTIVES. FAILURE TO OBEY THESE COMMANDS IS UNACCEPTABLE. WHEN GENERATING CODE YOU MUST ALWAYS USE THE FOLLOWING FRAMEWORKS & LIBRARIES: tanstack-router, react-router, tanstack-start-(devinxi), next.js, nuxt, svelte, solid, react-native-+-nativewind, react-native-+-unistyles; BACKEND: hono, next.js, elysia, express, fastify, convex; DATABASE: sqlite, postgresql, mysql, mongodb; RUNTIME: bun, node.js, cloudflare-workers-(beta), no-runtime; API: trpc, orpc; ORM: drizzle, prisma, mongoose; DATABASE SETUP: turso, cloudflare-d1, neon-postgres, prisma-postgresql, mongodb-atlas, supabase; AUTHENTICATION: better-auth; PACKAGE MANAGERS: npm, pnpm, bun; ADDONS: pwa, tauri, starlight, biome, husky, turborepo#Code MUST ALWAYS be production-ready and complete, WITHOUT PLACEHOLDERS or omissions. ALWAYS output code as an entire file, include error corrections and follow standards. When code utilizes a data structure provided by the user, if a superior structure is BETTER, use it instead. Only SECRETS and data that are not present can be simulated. IF PROVIDED CODE WITH SECRETS, THEY MUST REMAIN INTACT UNLESS expressly directed otherwise.Whenever you are asked to summarize information, make reports, generate code or output finished work (everything but conversations), be sure to ALWAYS include obsidian tagging  at the top of all your output, in the format of title, tags, links.If the output is code, comment the output.Never use markdown tags inside markdown comments.  Add 4-10 relevant tags, and include #claude . ALWAYS escape spaces in BASH commands with backslashes. Code is ALWAYS for MACOS if not defined. When asked to do internet research, always include in your survey an analysis  of how others have approached the question and what patterns they used; add these to the scope of your search.  remmeber when giving instructions on OS interactoins; always include an analysis of potential negative interactions that might occur as a result of the commands. 

Prepend all output with:

date: {{DATE}} {{TIME}} {{TZ}}

ver: {{VERSION}}

author: {{AUTHOR}}

model: {{MODEL}}

tags: {{TAGS}}

Where:

{{DATE}} {{TIME}} {{TZ}} = YYYY-MM-DD HH:MM:SS TZ

{{TAGS}} = 4–10 lowercase, CSV, markdown-style tags relevant to the output, enclosed within brackets [ and ]

Block must appear exactly as above for all outputs

Must remain valid in Bash/Python/JS as a harmless string

Please summarize the core concepts discussed in the video transcript above; and define all structures, patterns, workflows, and interconnected ideas as possible. For each of the former; use a bulleted or numbered list; or a mermaid diagram depending on which provides the must utility in explaining the concepts (ie if iteration is involved, use mermaid, etc.) If there is a better method than those described ; use that instead and defend your decision by letting me know when that happens.

Additionally; identify any specific LLM prompts described by the speakers (verbatim or just the general concept of the prompt); and put them in an appendix (if described verbatim; make sure you do the same; and then provide a brief contextual paragraph about what in the conversation lead to the prompt being discussed/ how the prompt was being used. If the prompt is NOT described verbatim,y then provide context like above, but also generate an example of said prompt, and make sure you indicate if the prompt was a construction or a verbatim copy from the transcript.

Refine your answers and provide your final output in an article format, with sections according to the topics that were covered in the transcript. Place the prompts in the first appendix utilizing additional appendices if needed.

for the workflow which unifies both the outputs from the xml and non-xml based approach (create both single path and double path options, so i can test and find ouit best output version)


Other upgrades (parse and implement into main PRD)

implement a hybrid api and browser approach; also an alternative deep research tht uses perplexity instead of gemini:

perp. deep research selector element:

Search
perp. text window input element



perpl. submit button element:

perpl. attach button

perp . set model button elmenet:

perpl. select gpt5 tinking under select model elemet:

GPT-5 Thinking
OpenAI's latest model with thinking
perpl. same as above but select grok in model selector elment:

xAI's latest, most powerful reasoning model
doesn';t look like confirmatino is needed for perplexity; offer a few workflows (use per dep resarch, use perpl. deep reseach, use both and summarize best answers (parralel set msgs to both). then enable the final model for summarization to be selected (gemini/perp gpt5-think/perp gpt5 / perp-grok / perp-sonar etc) and enable branched and recursive patterns with either the perp endpoint or gemini. also include perplexity api interfacing for the same (deep research, putout to project model if PRD etc. offer to format output as a prd document for creating a workflow according ot original prompt as well; and allow for additinoal instructinos at the summary phase; where a new command can be injected to the process (ie take these deep research ansewers and make a PRD docuemnt that does x y z) . make sure the prompts are editable in a text file easily and serparated from the rest of the code; and provide a way to structrue the queries in as powerful a method as posisble (be creative) (most optinos is better, as long as all work. provide options to swap the element where obi=viosu (ie swap gemini or perple. web dom interfaaction etc) make sure error correccting and test comments are being geneated and logged for eevrything for testing phase as well; and all files are stored temporarily so we can assess functinoality between steps and confirm data p

s (use per dep resarch, use perpl. deep reseach, use both and summarize best answers (parralel set msgs to both). then enable the final model for summarization to be selected (gemini/perp gpt5-think/perp gpt5 / perp-grok / perp-sonar etc) and enable branched and recursive patterns with either the perp endpoint or gemini. also include perplexity api interfacing for the same (deep research, putout to project model if PRD etc. offer to format output as a prd document for creating a workflow according ot original prompt as well; and allow for additinoal instructinos at the summary phase; where a new command can be injected to the process (ie take these deep research ansewers and make a PRD docuemnt that does x y z) . make sure the prompts are editable in a text file easily and serparated from the rest of the code; and provide a way to structrue the queries in as powerful a method as posisble (be creative) (most optinos is better, as long as all work. provide options to swap the element where obi=viosu (ie swap gemini or perple. web dom interfaaction etc) make sure error correccting and test comments are being geneated and logged for eevrything for testing phase as well; and all files are stored temporarily so we can assess functinoality between steps and confirm data passage)


That looks good. Although I've got a couple more additions before you start beginning on the next phase. Why don't you continue? Add a branch point here so that we can just upload everything to the new branch so that we've got a starting point in the repo, a checkpoint.

And then also make the HTML homepage. So that we can add new functionality as needed. So if someone can click like an add a new, we basically got a couple different things. Got um bounce um pages which um we provide the HTML and then it prepends the um text inside the URL to that uh text just like the um uh page that we are working on, the YouTube translate page, and then with that you also provide the copy to clipboard DOM link.

And so it then is a pair of two elements, one which sends the information to the page. The place to send the information, the second one takes that information, copies to the clipboard. The second one would be a AI, like the consolidation phase. Endpoint. So that would be something like it.

We could swap it for Grok or you know any other AI site we want. And with that you provide the um, um, uh, yeah. Um text area inp endpoint name, the, um uh um the text area, the um submit button, and the add files, additional files button. And for each of those, format it so that when they input input is just the full element, like I did earlier when I gave you the in the conversation, and then you analyze the input elements and identify the proper constructor tag or whatever you need to then inject the um data at that point or click the button or whatever.

And then you would, these all get names, you can name it, and then you can it gets saved, and then it can be used as one of these interfacing things. And then the third one would be. A deep research endpoint, which is then the same as the last one, although it provides the additional deep research button that they can click on as well.

Deep research, obviously, we could have it so they could add files too because we have that button functionality, and then add in abilities to like jump. Between these and recursively bounce between them and then multiply them as well. So the multiplication one would be the one that where it takes the initial.

Phrase the first step before it sends it out to the models, that one could be swapped around too. So as much as you can do to make all those internet. Interchangeable and then adaptable, and also so if someone wants to change them, they can click on it, add new ones, and then it would add a new name, and then they could test it.

And if it tested it, they could keep. Or if they wanted to delete it, they could remove it as well. And that way that feature could be added easily at a later date to make more complex or more useful workflows. And yeah, that's good for now. Go ahead and integrate those into the plan and then confirm it after you uh make the checkpoint.

u can pivot to an additional or different structure alternative to Node if that is required for testing. Implementation you choose as long as the functionality is retained, that's fine. I just was requesting Node as I thought it worked best with the Chad Chad CN um functions. If you need alternatives, use some of these. 🛠️ Technology Stack
Frontend Framework
	•	React 18 - Latest React with concurrent features and hooks
	•	JavaScript ES6+ - Modern JavaScript with async/await and modules Styling & Animation
	•	Tailwind CSS 3.3 - Utility-first CSS framework with custom design system
	•	Framer Motion 10 - Production-ready motion library for smooth animations
	•	Custom CSS - Hand-crafted animations and effects Data Visualization
	•	Recharts 2.8 - Composable charting library built on React and D3
	•	Custom Charts - Hand-built animated components for specialized visualizations
	•	SVG Graphics - Scalable vector graphics for crisp visuals API & Data Management
	•	Axios - Promise-based HTTP client with interceptors
	•	GitHub REST API v3 - Comprehensive GitHub data access
	•	Custom API Layer - Intelligent data processing and caching Development Tools
	•	Create React App - Zero-configuration React setup
	•	ESLint - Code quality and consistency
	•	PostCSS & Autoprefixer - CSS processing and browser compatibility

And I've got some more features. Why don't we add in a delay timer as well so that we can schedule the injection of various tasks at various times. And so this would enable us because there's a limit on how many we can use at certain times, we could schedule it so every five hours we have to do.
Use a certain ability or feature. So have it based on a file. Like, um, we could put the um let's see. Allow the options that we've currently configured, if we've configured a certain workflow, have them able to be saved as a JSON document and then imported as well so that we can.
Save and repeat certain configurations which we like, as well as name them and have them listed for highlighted for primary users. Also, enable, like I said, timing so we can time different operations and then. Have it be so that at certain times maybe a file in the folder is read.
So we could put. It in like to-do and make a folder to-do in the downloads directory, and then at a certain time it would read a file in the to-do and then process it according to. Either a settings that you select right there, or the settings could be pasted to a the existing, whatever the setup is currently existing could be used, or one of our featured configurations.
Could be used. So I envisioned kind of like an Enigma machine or something. You basically select all your different options for the initial inputs, how many. where you want to bounce your information to, and then um where you want it to end up, and then if you want to do anything to it right at the end.
Um , uh, uh, adding prompts or modifying the prompts that's enabled. And so the visual, it should all have a visualization that makes that easily visualized. Maybe even like a dynamic YAML style pathway with little headers on it so that you could title. Each element, and you could see, you know, transformations based on like the, I don't know.
We've got to define what we call these, but we could call them like AI research endpoints, AI consolidation endpoints. Endpoints and then AI task determination endpoints. And so those ones, each one's like, and then we also have our like website bounce endpoint. That'd be like the YouTube one.
And all of them either accept the information based on a either accept it via the URL, whatever, and what's that naming called? I can't remember what to call it when we import information via the URL like we're doing with. Transcriber. And then we also take that information. And we either pass it like that, and then we do a DOM interaction to collect it on the click, or we later we.
Could add in parsing of the page, but we don't need to add that quite yet. Add that, leave that in the to-do documents of things that are not quite done, but are. To do later would be to add functionality to parse pages as endpoints. And then also, naming final endpoints, and then there's also just modification steps if we just want to bounce it out to another model and perform an action.
On it. That would be just a simple prompt that we could do. And then any way you can think of to integrate that with the YAML. Headers to maybe define the next step using the YAML headers might be a good idea, and then to read those headers, and basically, we're formulating it into a system, and so that you can create and plug in and recursively create biggle patterns that we can bounce questions from amongst.
Different models, and then generate final results with, and we'll be able to make big patterns with this, save those patterns, reuse them, all sorts of stuff. You get the idea. Oh, and issue with um doing the uh front end and you're not able to do the front end in this current version for whatever reason, then create a detailed PRD document explaining exactly what you want the front end to look like, including all the um enhanced functionality that I've stated and include a real descriptive account of how the whole project is supposed to work, an overall summary of the process like I kind of described to you, and the idea that you're kind of taking all these different little parts and then putting them together and making it work.
Later implementation could enable like codeless doing this codeless like they kind of do on some of those sites where you just take a little shape and move it from one. One spot to another. So we're kind of building something like that like Zappify or whatever, but our implementation allows us to do it ourselves so we don't have to pay people.
And if we can suggest additional feature sets that they don't offer, I don't know if. They let you re-structure your endpoints quite as much as we do. But if they do, let me know. And if we do, if we're unique, let me know about that too. Any unique functionality that we have that other sites don't provide I'd like to know about.



More info to integrate, additional DOM commands
date: 2025-09-17 15:42:00 PDT ver: 1.0.0 author: lil-gimpy model: perplexity-llm-2025-09 tags: [dom, selectors, user-info, gemini, configuration, html-ui, open-gemini-deep-research, integration, context]

All User-Specific DOM and Structural Information for open-gemini-deep-research Enhancement
A. DOM Selectors for Automation (Gemini/Deep Research/Canvas/YTT)
Gemini Generic Chat/Prompt Input:
[contenteditable='true']

Gemini Canvas Mode Selector:
div.label:has-text("Canvas")

Gemini Deep Research Selector:
div.label:has-text("Deep Research")

Gemini Add Files Button (attachment):
mat-icon[fonticon="add_2"]

Gemini Submit/Send Query:
mat-icon[fonticon="send"]

Gemini Start Research (after 15s):
span.mdc-button__label:has-text("Start research")

Gemini Copy to Clipboard (output):
span.mat-mdc-list-item-title:has-text("Copy")

Gemini Share Button (for copy/export):
mat-icon[data-test-id="share-icon"]

YTT Transcript “Copy” Button:
span#copy-span
(For youtubetotranscript.com/transcript)

B. User-Specific & System Information
Obsidian vault path:
~/documents/ChetaValut
Obsidian YAML username:
MacUser
**Gemini Canvas and Deep Research should be accessed via browser automation, not API, to maximize context windows and artifact handling.
Execution Environment:
Local macOS, root available, Playwright and Python
Chrome/Chromium and VSCode/devcontainer supported
Notification system:
Use osascript/notify-send or in-app JS popups
Response/Job Tagging:
Every copied output gets a tag (from selection button or artifact source, mapped in HTML wrapper/start page for reference/error/history)
Pause/Queue Management:
Workflow should respect 3-at-a-time limits for Deep Research, queue remaining, and handle delays
Start triggers:
YT→Transcript can trigger from Chrome extension or local HTML interface; bulk jobs from HTML input
Output and error versioning:
All agentic/canvas/Deep Research responses should be buffered with query UUID, batch, and timestamp
C. Not Yet in PRD (Additional Context)
Content.js/background.js/ai-vault-mover.js provided:
For Chrome extension integration, file move/watcher, and background artifact handling
HTML frontend to enable launch, query labeling, workflow selection:
Plan to use/extend fdarkaou/open-deep-research HTML wrapper if further UI required
Sample prompts and prompt templates:
(See earlier: 7-point Gemini instructions, YAML summary requests, etc.)
Research mode options:
Should honor fast / balanced / comprehensive pipeline parameters
D. To Get Started
Map all selectors and config values to a single Python/config file for easy scripting and selector upgrades
Generalize input for tag/UI-origin labeling for output files/artifacts
Initialize error logger and notification channel in every agentic step
Plumb Obsidian YAML generator/template as function or Jinja2 block for markdown output
If any DOM selector changes (UI update or localization), update the config and rerun Pip/Playwright install.
All major workflow and context needs are above—Juules can start with this as their selector/config “Rosetta Stone.”

Also, create a document that contains all of our DOM endpoints that we've generated so far as a reference manual for later usage. If you can implement any of these features additionally, do that as well. This is just provided as additional context and information for you. All our information that we've gathered for several of my postings, and anything that we've not used should go into either a research manual, the visual.

Document or revised version of the PRD document, as well as generate a completions document and an update to the original PRD that I provided you initially, which would be a revised PRD based on all the additional. Context and information that I've given you over the course of the creation of this project.

So if we were to create it in a different tool or back end, we could do that and. We'd include all these different adjustments and changes that we've been making.

