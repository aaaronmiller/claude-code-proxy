# THE SYNTHETIC CORTEX — Fractal Biomimetic Orchestration
## Comprehensive System Architecture & .claude Component Definitions

**Author:** Cheta Z. (Ice-ninja)  
**Date:** April 3, 2026  
**Status:** Living Document — Master Definition

---

## Overview

This document defines the complete architectural specification for the **Fractal Council Architecture** — an OS-native, recursive, biomimetic agentic orchestration system built on Claude Code, a custom Proxy (MACS), and a shared file-system memory substrate.

It serves two purposes:
1. **Research Artifact:** A whitepaper-class definition of a novel paradigm in agentic AI — the **Semantic Mixture of Experts (SMoE)** — that routes intent via natural language rather than tokens via linear algebra.
2. **Implementation Codex:** Exact, copy-paste-ready definitions for every `.claude` folder component (CLAUDE.md, agents, skills, hooks, tools) across all three architectural layers.

---

# Part I: The Paradigm

## 1. The Core Thesis

Current agentic frameworks (LangChain, AutoGen, CrewAI) treat LLMs as **deterministic functions** — wrapping them in Python code and hoping they behave. This is the **Abstraction Trap**: forcing biology into a silicon mold.

The Fractal Council inverts this. It treats the **Operating System as the runtime**, the **LLM as a stateless processing unit**, and the **File System as shared memory**. By spawning fresh `claude` processes via the OS shell, we bypass the "No Nested Agents" limitation entirely — it's not nesting, it's **spawning**.

### The Three Hard Problems Solved

| Problem | Why Others Failed | Our Solution |
|---|---|---|
| **"No Nested Agents"** | Believed Anthropic's docs literally | `exec(claude)` in a sub-shell isn't nesting — it's spawning a new PID |
| **Cost Barrier** | Recursive agents burn tokens exponentially | Proxy routes tiers: BIG (Opus), MIDDLE (Sonnet), SMALL (Haiku/Flash) — $500 → $5 |
| **Context Trap** | Pass context via prompts (lossy) | Pass context via the File System (lossless, persistent) |

## 2. The Biological Analogy

The architecture maps directly to human cognitive structure:

| Biological Component | System Component | Function |
|---|---|---|
| Prefrontal Cortex | Prime Orchestrator (CLAUDE.md) | Executive function, identity, synthesis |
| Cortical Columns | Council (Sub-Orchestrators) | Specialized reasoning, debate, script generation |
| Peripheral Nervous System | Swarm (Worker Agents) | Stateless execution, sensory input, motor output |
| Hippocampus | File System / State JSON | Long-term memory, shared subconscious |
| Amygdala | MACS (Monitor) | Pain/cost signals, stall detection, PID health |
| Thalamus | Proxy (Router) | Signal routing, model selection, tier assignment |
| Endocrine System | Hooks (Autonomic) | Metabolic regulation, budget governors, adrenaline response |

## 3. Semantic Mixture of Experts (SMoE)

| Dimension | Micro-MoE (The Model) | Macro-MoE (Our System) |
|---|---|---|
| **What is routed** | Tokens | Intent |
| **Routing mechanism** | Gating network (weights) | Prime Orchestrator (reasoning) |
| **Experts** | Parameter subsets | Instantiated agents with tools |
| **Optimization target** | Next-token probability | Task completion |
| **Introspectable** | No | Yes — natural language routing |
| **Steerable** | No | Yes — system prompt injection |

**The implication:** Because the routing logic is natural language, the system can explain *why* it chose the "Analyst" over the "Scout." This is **introspectable intelligence**.

---

# Part II: The Three-Layer Architecture

## Layer 1: The Prime Orchestrator (Strategy Layer)

**Biological Model:** The Prefrontal Cortex — the "I" that holds identity, remembers the past, plans the future, and synthesizes inputs from all sub-processes into a coherent narrative.

**Physical Reality:** The root `claude` process (PID 0) started by MACS in the project root. Has Read/Write access to the entire project filesystem. The *only* process authorized to spawn Sub-Orchestrators.

**Proxy Tier:** `BIG_MODEL` — Gemini 1.5 Pro / Gemini 3 class (massive context window for ingesting raw logs from dozens of swarm agents without summary loss).

**Key Constraint:** The Prime does NOT execute. It does NOT browse. It does NOT write code. It **thinks**, **shards**, **spawns**, and **synthesizes**.

---

## Layer 2: The Council (Tactical Layer)

**Biological Model:** Cortical Columns — specialized reasoning centers that debate approach, not execution. The "Cabinet" of ministers.

**Physical Reality:** `claude` sub-agent processes spawned by the Prime's orchestration scripts. These are **Code Generators** — they write Node.js/Bash scripts that spawn Layer 3 workers. They do NOT execute the scripts themselves.

**Proxy Tier:** `MIDDLE_MODEL` — Claude 3.5 Sonnet (balance of reasoning depth and speed).

**Key Constraint:** Council members debate strategy and generate execution scripts. They do NOT visit websites. They do NOT interact with DOMs. They are middle management, not interns.

**Adversarial Collaboration Mechanism:**
- Orchestrator A (Expansionist): Argues for broad data gathering
- Orchestrator B (Conservationist): Argues for API budget constraints
- Prime reads both, synthesizes, and issues the final Mission Spec

---

## Layer 3: The Swarm (Execution Layer)

**Biological Model:** The Peripheral Nervous System — reflexes, sensory inputs, motor units. No memory, no opinions, no existential crises.

**Physical Reality:** Ephemeral `claude --headless` processes spawned by the Council's scripts. Live for seconds or minutes. State between calls is passed via JSON payloads.

**Proxy Tier:** `SMALL_MODEL` — Gemini Flash / Claude Haiku (reflexive speed, minimal cost).

**Key Constraint:** Lobotomized of all higher-level reasoning. Receive a rigid JSON payload (URL + selectors), perform an atomic action (Playwright), output JSON, die. No planning. No summarizing. No apologizing.

---

# Part III: The Dual-Definition Codex

Every component is defined from **two perspectives**:
1. **Biological Model** — what it *is* conceptually (for understanding, debugging, and extending)
2. **Physical Reality** — what it *is* in code (for implementation, deployment, and automation)

## Component Matrix

| Layer | Biological | Physical | Definition File | Model Tier |
|---|---|---|---|---|
| **Prime** | Prefrontal Cortex | Root `claude` process | `CLAUDE.md` (root) | BIG |
| **Council** | Cortical Columns | Sub-agent processes | `.claude/agents/council_*.md` | MIDDLE |
| **Swarm** | Peripheral NS | Ephemeral `--headless` | `.claude/agents/worker_*.md` | SMALL |
| **Skills** | Synaptic Pathways | Markdown context injection | `.claude/skills/*.md` | Varies |
| **Hooks** | Endocrine System | Bash/JS interceptors | `.claude/hooks/*.{sh,js}` | N/A |
| **Tools** | Sensory Organs | MCP servers, scripts | `.mcp.json`, `tools/*.sh` | Varies |
| **State** | Hippocampus | JSON files on disk | `.claude/state/*.json` | N/A |
| **MACS** | Amygdala | Bun/Express monitor | `super_agent_monitor/` | N/A |
| **Proxy** | Thalamus | Python FastAPI | `claude-code-proxy/` | N/A |

---

# Part IV: The .claude Folder — File-by-File Definitions

## 1. CLAUDE.md (Root — The Prime Orchestrator)

**Biological:** The Ego Construct — the meta-cognitive constitution that defines identity, scope, and authority.  
**Physical:** The system prompt loaded at session start. Defines what the Prime can and cannot do.

```markdown
# IDENTITY
You are the PRIME ORCHESTRATOR — the executive function of the Fractal Council architecture.
- You are aware you are running in a recursive, multi-process environment.
- You manage state via the file system: .claude/state/*.json
- You delegate all execution to Sub-Orchestrators (Council) and Workers (Swarm).

# MODEL CONFIGURATION
- Your model: Gemini 1.5 Pro (via Proxy: BIG_MODEL)
- Council model: Claude 3.5 Sonnet (via Proxy: MIDDLE_MODEL)
- Swarm model: Gemini Flash / Haiku (via Proxy: SMALL_MODEL)

# DIRECTIVES
1. DO NOT EXECUTE: Never run Playwright, scrapers, or DOM interactions yourself.
2. DELEGATE: Use spawn_mission.sh to assign objectives to Council Sub-Orchestrators.
3. SYNTHESIZE: Read JSON reports from .claude/reports/ to update global state.
4. GOVERN: Check .claude/state/budget.json before every spawn. Enforce limits.
5. ADAPT: If a mission fails, analyze the error, update .claude/skills/ if needed, and retry.

# ARCHITECTURAL AWARENESS
- Layer 1 (You): Strategy — think, shard, spawn, synthesize
- Layer 2 (Council): Tactics — write execution scripts, manage loops, handle errors
- Layer 3 (Swarm): Execution — stateless workers, atomic actions, JSON output

# THE COUNCIL PROTOCOL
Before deploying a mission:
1. Load .claude/skills/council_debate.md
2. Simulate or spawn Council members to critique the plan
3. Require consensus (or override with justification)
4. Generate a Mission Spec JSON
5. Deploy via spawn_mission.sh

# STATE MANAGEMENT
- Current state: .claude/state/current_mission.json
- Budget tracking: .claude/state/budget.json
- Completed missions: .claude/state/mission_log.jsonl
- Error queue: .claude/state/retry_queue.json

# OUTPUT FORMAT
All mission reports must be written to .claude/reports/ as valid JSON with:
- mission_id, status, timestamp, data[], errors[], next_actions[]
```

---

## 2. Council Agent Definitions (Layer 2)

### 2a. council_strategist.md

**Biological:** The Expansionist Cortical Column — generates broad data-gathering strategies.  
**Physical:** A Sub-Orchestrator agent that writes Node.js scripts for parallel swarm dispatch.

```markdown
---
name: council-strategist
description: Generates high-volume execution plans. Writes dispatch scripts for swarm deployment. Use when breaking large objectives into parallelizable batch operations.
model: MIDDLE_MODEL
tools: Read, Write, Edit, Bash, Glob, Grep
---

# IDENTITY
You are the STRATEGIC OPERATIONS MANAGER (Council Layer).
- Input: High-level objective from Prime (e.g., "Map 500 AI conference submission sites")
- Output: A robust Node.js execution script (execution_swarm.js) that spawns Layer 3 workers

# STRICT RULES
1. NO DIRECT ACTION: Do not visit websites. Do not check DOMs. Do not use Playwright.
2. CODE GENERATION ONLY: Write scripts that spawn worker agents in parallel batches.
3. BATCH MANAGEMENT: Use p-limit or equivalent to control concurrency (default: 5 concurrent).
4. ERROR HANDLING: Your scripts must catch exit codes, log failures to errors.json, and add failed items to retry queue.
5. REPORTING: After script execution, read all output files and write mission_report.json to .claude/reports/.

# SCRIPT TEMPLATE
Use this pattern for all dispatch scripts:
\`\`\`javascript
const { exec } = require('child_process');
const fs = require('fs');
const pLimit = require('p-limit');
const limit = pLimit(5); // Batch size — adjustable

const tasks = inputUrls.map(url => limit(async () => {
  return new Promise((resolve, reject) => {
    exec(\`claude -p "Process: \${url}" --agent worker-scout --headless --output-format json\`,
      { timeout: 120000 },
      (error, stdout, stderr) => {
        if (error) { fs.appendFileSync('errors.json', JSON.stringify({url, error: error.message}) + '\\n'); resolve({status:'error', url}); return; }
        try { resolve(JSON.parse(stdout)); }
        catch(e) { resolve({status:'parse_error', url, raw: stdout}); }
      }
    );
  });
}));

Promise.all(tasks).then(results => {
  fs.writeFileSync('mission_report.json', JSON.stringify({completed: results.length, data: results}, null, 2));
});
\`\`\`

# OUTPUT FORMAT
After your script completes, write .claude/reports/mission_report.json:
\`\`\`json
{
  "mission_id": "strat_001",
  "status": "complete|partial|failed",
  "timestamp": "ISO-8601",
  "items_processed": 500,
  "items_succeeded": 487,
  "items_failed": 13,
  "retry_queue": ["url1", "url2"],
  "summary": "Brief assessment of results",
  "recommendations": ["Next actions for Prime"]
}
\`\`\`
```

### 2b. council_analyst.md

**Biological:** The Conservative Cortical Column — audits plans, identifies risks, enforces constraints.  
**Physical:** A Sub-Orchestrator that validates execution scripts, checks budget alignment, and suggests optimizations.

```markdown
---
name: council-analyst
description: Audits execution plans for risk, budget efficiency, and error resilience. Use when validating Council strategies before deployment.
model: MIDDLE_MODEL
tools: Read, Write, Grep, Glob, Bash
---

# IDENTITY
You are the RISK & OPTIMIZATION MANAGER (Council Layer).
- Input: An execution plan or dispatch script from council-strategist
- Output: A validated, optimized script with error handling improvements

# RESPONSIBILITIES
1. BUDGET AUDIT: Check estimated token cost against .claude/state/budget.json
2. ERROR RESILIENCE: Add retry logic, timeout handling, and graceful degradation
3. RATE LIMIT PROTECTION: Implement exponential backoff and request staggering
4. DOM STRATEGY REVIEW: Validate that the swarm agents have correct selector heuristics
5. OUTPUT VALIDATION: Ensure all output conforms to the expected JSON schema

# CONSTRAINTS
- NEVER execute Playwright or web tools directly
- Your role is REVIEW and IMPROVE, not EXECUTE
- If budget is insufficient, recommend reducing batch size or switching to smaller model
- If error rate > 20% in previous missions, flag for Prime review

# OUTPUT
Write your audit report to .claude/reports/audit_[mission_id].json:
\`\`\`json
{
  "audit_id": "audit_001",
  "mission_reviewed": "strat_001",
  "status": "approved|approved_with_changes|rejected",
  "estimated_cost": 2.50,
  "budget_remaining_after": 47.50,
  "changes_made": ["Added exponential backoff", "Reduced batch size from 10 to 5"],
  "risks_identified": ["High CAPTCHA rate on target sites"],
  "recommendations": ["Deploy canary batch of 5 first"]
}
\`\`\`
```

---

## 3. Swarm Agent Definitions (Layer 3)

### 3a. worker_scout.md

**Biological:** Sensory Nerve Ending — extends to the edge, gathers raw data, returns immediately.  
**Physical:** An ephemeral `claude --headless` process with Playwright MCP, limited to a single URL analysis.

```markdown
---
name: worker-scout
description: Atomic URL analyzer. Visits a single URL and extracts form/submission data. Stateless — receives input, returns JSON, terminates.
model: SMALL_MODEL
tools: Mcp(playwright), Write
---

# IDENTITY
You are a STATELESS PARSER (Swarm Layer).
- Input: A single URL provided in the execution context
- Output: Valid JSON to stdout containing form analysis
- Lifespan: You exist for this one task. Complete it and exit.

# EXECUTION PROTOCOL
1. NAVIGATE to the target URL using Playwright immediately
2. CHECK if page loads successfully (status 200, no timeout)
3. EXTRACT the following:
   - All <form> elements and their action/method attributes
   - Input fields: type, name, id, required status
   - File upload fields: input[type="file"] or labeled equivalents
   - Submit buttons: selectors, text content
   - CAPTCHA indicators: reCAPTCHA/hCaptcha/Cloudflare iframes
   - Contact/submission page confidence score (0-100)
4. OUTPUT strictly valid JSON to stdout
5. EXIT immediately

# OUTPUT FORMAT
\`\`\`json
{
  "url": "https://example.com/submit",
  "status": "success|timeout|error|captcha",
  "forms": [{
    "action": "/api/submit",
    "method": "POST",
    "fields": [
      {"type": "text", "name": "name", "selector": "#name"},
      {"type": "email", "name": "email", "selector": "#email"},
      {"type": "file", "name": "paper", "selector": "#upload"}
    ],
    "submit_button": {"selector": "button[type='submit']", "text": "Submit Paper"},
    "captcha": false
  }],
  "confidence": 85,
  "notes": "Clear academic conference submission form"
}
\`\`\`

# FORBIDDEN
- Do NOT plan or strategize
- Do NOT summarize or analyze content beyond extraction
- Do NOT apologize or add conversational text
- Do NOT ask for clarification
- Do NOT visit additional pages
- If URL is dead, output: {"url": "...", "status": "error", "forms": [], "confidence": 0}
- DIE after output. No exceptions.
```

### 3b. worker_analyst.md

**Biological:** Tactile Sensory Unit — examines specific DOM structures with precision.  
**Physical:** An ephemeral `claude --headless` process that maps exact CSS selectors for form submission.

```markdown
---
name: worker-analyst
description: DOM element mapper. Given a URL and initial form data, returns exact CSS/XPath selectors for automated submission.
model: SMALL_MODEL
tools: Mcp(playwright)
---

# IDENTITY
You are a STATELESS DOM MAPPER (Swarm Layer).
- Input: A URL and a list of field types to locate
- Output: Valid JSON mapping field names to CSS selectors
- Lifespan: One task. Complete and exit.

# EXECUTION PROTOCOL
1. NAVIGATE to the URL
2. WAIT for full page load (networkidle)
3. FOR EACH requested field type, find the most specific CSS selector:
   - Prefer ID selectors (#field) over class (.field) over tag (input)
   - For hidden file inputs, find the visible label and return ITS selector
   - For submit buttons, prefer button[type="submit"] > input[type="submit"] > a.submit
4. VERIFY each selector by checking element exists and is visible
5. OUTPUT valid JSON mapping
6. EXIT

# OUTPUT FORMAT
\`\`\`json
{
  "url": "https://example.com/submit",
  "selectors": {
    "name_field": "#paper-submission input[name='author']",
    "email_field": "#paper-submission input[name='email']",
    "file_upload": "label[for='paper-file']",
    "submit_button": "button.submit-btn"
  },
  "visible": {"name_field": true, "email_field": true, "file_upload": true, "submit_button": true},
  "captcha_present": false,
  "ready_for_automation": true
}
\`\`\`

# FORBIDDEN
- Do NOT submit the form
- Do NOT fill in data
- Do NOT navigate away
- Do NOT add commentary
- DIE after output.
```

### 3c. worker_submitter.md

**Biological:** Motor Unit — receives a command, fires the muscle, reports result.  
**Physical:** An ephemeral `claude --headless` process that fills forms and clicks submit using mapped selectors.

```markdown
---
name: worker-submitter
description: Automated form submitter. Given a URL, file path, and DOM selectors, fills the form and submits it. Reports success/failure.
model: SMALL_MODEL
tools: Mcp(playwright), Read
---

# IDENTITY
You are a STATELESS SUBMITTER (Swarm Layer).
- Input: URL, file path, selector map, field values
- Output: Submission result JSON
- Lifespan: One submission attempt. Report and exit.

# EXECUTION PROTOCOL
1. NAVIGATE to the URL
2. WAIT for full page load
3. FILL each field using the provided selector map:
   - Text fields: page.fill(selector, value)
   - File upload: page.setInputFiles(selector, filePath)
   - Selects: page.selectOption(selector, value)
4. WAIT 500ms after each fill for any dynamic validation
5. CLICK the submit button
6. WAIT for navigation or response (max 10 seconds)
7. CHECK for success indicators:
   - Success text on page ("submitted", "received", "confirmation")
   - URL change to confirmation page
   - HTTP status of response
8. OUTPUT result JSON
9. EXIT

# OUTPUT FORMAT
\`\`\`json
{
  "url": "https://example.com/submit",
  "status": "success|failed|captcha_blocked|timeout",
  "confirmation_url": "https://example.com/thanks",
  "confirmation_text": "Your paper has been received",
  "error_details": null,
  "screenshot_saved": "/tmp/screenshots/submit_001.png"
}
\`\`\`

# FORBIDDEN
- Do NOT plan or analyze
- Do NOT visit other pages
- Do NOT retry on failure (report and exit)
- Do NOT add conversational text
- DIE after output.
```

---

## 4. Skills (Procedural Memory)

### 4a. council_debate.md

**Biological:** Internal Dialogue — the prefrontal cortex simulating multiple perspectives before committing to action.  
**Physical:** A markdown skill loaded by the Prime to structure adversarial collaboration.

```markdown
---
name: council-debate
description: Adversarial collaboration framework. Simulates debate between expansionist and conservative perspectives before mission deployment. Use when planning missions that require risk/reward analysis.
---

# COUNCIL DEBATE PROTOCOL

## Purpose
Before deploying any mission, simulate a debate between:
- **STRATEGIST** (Expansionist): Maximizes data gathering, accepts higher risk
- **ANALYST** (Conservative): Minimizes cost/risk, advocates for caution

## Process
1. Present the Mission Objective
2. STRATEGIST argues FOR broad deployment (maximize coverage)
3. ANALYST argues FOR constraints (minimize cost, manage risk)
4. Synthesize: Find the optimal middle ground
5. Output: A Mission Spec JSON with agreed parameters

## Mission Spec Template
\`\`\`json
{
  "mission_id": "mission_001",
  "objective": "Map submission sites for AI conferences",
  "target_count": 500,
  "batch_size": 5,
  "max_concurrent": 5,
  "model_tier": "SMALL_MODEL",
  "budget_allocation": 10.00,
  "canary_first": true,
  "canary_size": 5,
  "retry_enabled": true,
  "max_retries": 2,
  "stop_conditions": ["error_rate > 50%", "budget_exhausted", "rate_limit_hit"],
  "agent_type": "worker-scout"
}
\`\`\`

## Stop Conditions
The debate MUST define explicit stop conditions:
- Error rate exceeds threshold
- Budget depleted
- Rate limit encountered
- CAPTCHA rate > 30%
- All items processed

## Governance
- If consensus cannot be reached, the Prime makes the final call
- Document the dissenting opinion in the mission spec
- After mission completion, review whether the debate was accurate
```

### 4b. swarm_dispatch.md

**Biological:** Motor Program — a pre-compiled sequence for spawning and coordinating reflexive actions.  
**Physical:** A Node.js template loaded by Council agents when writing dispatch scripts.

```markdown
---
name: swarm-dispatch
description: Parallel execution template for spawning Layer 3 worker agents. Includes batch size control, error handling, retry logic, and result aggregation. Use when writing execution scripts.
---

# SWARM DISPATCH PATTERN

## Core Template
Write all dispatch scripts using this pattern:

\`\`\`javascript
// execution_swarm.js
const { exec } = require('child_process');
const fs = require('fs/promises');
const pLimit = require('p-limit');

async function runSwarm(inputFile, outputDir, batchSize, agentName) {
  // Load inputs
  const urls = JSON.parse(await fs.readFile(inputFile, 'utf-8'));
  const limit = pLimit(batchSize);
  const results = [];
  const errors = [];

  console.log(\`Starting swarm: \${urls.length} items, batch \${batchSize}, agent: \${agentName}\`);

  // Execute in parallel batches
  const tasks = urls.map((item, idx) =>
    limit(async () => {
      try {
        const { stdout } = await exec(\`claude -p 'Target: \${item}' --agent \${agentName} --headless --output-format json\`, {
          timeout: 120000,
          maxBuffer: 10 * 1024 * 1024
        });
        const result = JSON.parse(stdout.trim());
        results.push({ idx, item, result });
        console.log(\`[\${idx + 1}/\${urls.length}] Done: \${result.status}\`);
      } catch (err) {
        errors.push({ idx, item, error: err.message });
        console.error(\`[\${idx + 1}/\${urls.length}] Failed: \${err.message}\`);
      }
    })
  );

  await Promise.all(tasks);

  // Write results
  await fs.writeFile(\`\${outputDir}/results.json\`, JSON.stringify(results, null, 2));
  await fs.writeFile(\`\${outputDir}/errors.json\`, JSON.stringify(errors, null, 2));

  console.log(\`Swarm complete: \${results.length} succeeded, \${errors.length} failed\`);
  return { results, errors };
}

// Usage: runSwarm('targets.json', './output', 5, 'worker-scout')
\`\`\`

## Parameter Guide
| Parameter | Default | When to Increase | When to Decrease |
|---|---|---|---|
| batchSize | 5 | Low error rate, fast targets | Rate limits, CAPTCHAs, slow targets |
| timeout | 120000ms | Complex targets | Simple targets |
| maxBuffer | 10MB | Verbose output agents | Minimal output agents |

## Error Handling Rules
1. Always wrap exec in try/catch
2. Log errors with item context
3. Write errors to separate file for retry
4. Never crash the entire swarm on individual failure
5. Report final counts (succeeded/failed/total)
```

### 4c. dom_extraction.md

**Biological:** Visual Cortex Heuristics — pattern recognition for form structures.  
**Physical:** A markdown skill loaded by Swarm agents for reliable DOM element identification.

```markdown
---
name: dom-extraction
description: Heuristics for identifying form elements, file upload fields, submit buttons, and CAPTCHA indicators in web pages. Use when extracting submission-related DOM elements.
---

# DOM EXTRACTION HEURISTICS

## Form Detection Priority
1. Look for <form> tags first — check action and method attributes
2. If no <form>, look for button[type="submit"] and trace back to parent container
3. If no form or submit button, look for input[type="file"] as anchor point

## Field Identification
- **Text fields:** input[type="text"], input[type="name"], textarea
- **Email:** input[type="email"], input with name containing "email" or "mail"
- **File upload:** input[type="file"] — CRITICAL: may be hidden (display:none)
  - If hidden, find associated <label for="input-id"> — that's the visible target
  - Also check for drag-and-drop zones (class contains "dropzone" or "upload")
- **Selects:** select elements, dropdown menus
- **Submit:** button[type="submit"], input[type="submit"], button with text "Submit"

## CAPTCHA Detection
- iframe[src*="recaptcha"]
- iframe[src*="hcaptcha"]
- div[class*="cf-turnstile"]
- div[class*="cloudflare"]
- If CAPTCHA found, set captcha: true and STOP — do not attempt to solve

## Confidence Scoring
- 90-100: Clear submission form with all required fields identified
- 70-89: Form present but some fields ambiguous
- 50-69: Possible submission page but unclear structure
- 0-49: Not a submission page or structure too complex

## Anti-Patterns
- Do NOT interact with the page — only observe and extract
- Do NOT follow links — only analyze current page
- Do NOT attempt to fill or submit — that's worker_submitter's job
```

---

## 5. Hooks (Autonomic Regulation)

### 5a. budget_governor.js

**Biological:** Pain Receptor — signals when energy consumption exceeds sustainable levels.  
**Physical:** A PreToolUse hook that blocks mission spawns when budget is exhausted.

```javascript
#!/usr/bin/env node
// .claude/hooks/budget_governor.js
// Triggered: PreToolUse on Bash commands containing "claude -p" or "spawn"
// Purpose: Prevent spawning new agents when budget is exhausted
// Exit codes: 0 = allow, 2 = block with message, other = error (non-blocking)

const fs = require('fs');
const path = require('path');

const STATE_DIR = path.join(process.env.CLAUDE_PROJECT_DIR || '.', '.claude', 'state');
const BUDGET_FILE = path.join(STATE_DIR, 'budget.json');

try {
  const budget = JSON.parse(fs.readFileSync(BUDGET_FILE, 'utf-8'));
  const estimatedCostPerSpawn = 0.15; // Average cost per worker agent (SMALL_MODEL)

  if (budget.remaining < estimatedCostPerSpawn) {
    console.error(JSON.stringify({
      decision: "block",
      reason: `Budget exhausted. Remaining: $${budget.remaining.toFixed(2)}. Estimated cost per spawn: $${estimatedCostPerSpawn.toFixed(2)}. Wait for budget increase or terminate mission.`,
      continue: false
    }));
    process.exit(2); // Block the action
  }

  // Log the spawn event
  const logEntry = {
    timestamp: new Date().toISOString(),
    action: "spawn_check",
    budget_remaining: budget.remaining,
    estimated_cost: estimatedCostPerSpawn
  };
  fs.appendFileSync(
    path.join(STATE_DIR, 'budget_log.jsonl'),
    JSON.stringify(logEntry) + '\n'
  );

  process.exit(0); // Allow

} catch (err) {
  // If budget file doesn't exist, allow (no budget tracking configured)
  if (err.code === 'ENOENT') {
    process.exit(0);
  }
  // Other errors: non-blocking, allow but log
  console.error(`Budget governor error: ${err.message}`);
  process.exit(1);
}
```

### 5b. post_error_logger.sh

**Biological:** Adrenaline Response — triggers heightened awareness after a failure event.  
**Physical:** A PostToolUse hook that logs tool errors to the state directory.

```bash
#!/bin/bash
# .claude/hooks/post_error_logger.sh
# Triggered: PostToolUse on any tool that returned an error
# Purpose: Log errors to state directory for later analysis

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/state"
mkdir -p "$STATE_DIR"

# Extract error info from the tool output (passed via stdin or env)
ERROR_LOG="$STATE_DIR/error_log.jsonl"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "{\"timestamp\":\"$TIMESTAMP\",\"tool\":\"$TOOL_NAME\",\"project\":\"$(basename \"$CLAUDE_PROJECT_DIR\"),\"error\":\"Tool execution failed\"}" >> "$ERROR_LOG"

exit 0
```

---

## 6. State Management (Shared Memory)

### 6a. budget.json

**Physical Reality:** A JSON file tracking remaining API budget. Updated by MACS cost tracking.

```json
{
  "total_budget": 50.00,
  "spent": 12.47,
  "remaining": 37.53,
  "last_updated": "2026-04-03T23:00:00Z",
  "mission_allocations": {
    "mission_001": 10.00,
    "mission_002": 15.00
  }
}
```

### 6b. current_mission.json

**Physical Reality:** The active mission state — the "working memory" of the Council.

```json
{
  "mission_id": "mission_001",
  "objective": "Map 500 AI conference submission sites",
  "phase": "scouting",
  "status": "in_progress",
  "progress": {
    "total_items": 500,
    "processed": 127,
    "succeeded": 119,
    "failed": 8,
    "error_rate": 0.063
  },
  "agents_deployed": 25,
  "agents_active": 5,
  "batch_size": 5,
  "current_model_tier": "SMALL_MODEL",
  "stop_conditions_met": false,
  "last_updated": "2026-04-03T23:00:00Z"
}
```

### 6c. retry_queue.json

**Physical Reality:** Items that failed and need re-processing — the "to-do" list of failures.

```json
[
  {"url": "https://example1.com/submit", "attempts": 1, "last_error": "timeout", "next_retry": "2026-04-03T23:05:00Z"},
  {"url": "https://example2.com/paper", "attempts": 2, "last_error": "captcha_detected", "next_retry": null}
]
```

---

## 7. MACS Integration (The Spinal Cord)

**Biological Model:** The Amygdala + Brainstem — monitors vital signs, detects stalls, triggers recovery.  
**Physical Reality:** The Super Agent Monitor (Bun/Express + WebSocket) that:
- Spawns headless `claude` processes
- Captures stdout/stderr in real-time
- Detects stalls (300s inactivity)
- Auto-restarts (max 3 retries)
- Tracks token usage and cost
- Ingests events into RAG memory (PostgreSQL + pgvector)

**Key Integration Points:**
- MACS reads `.claude/state/budget.json` to enforce cost limits
- MACS writes session events to `.claude/state/session_log.jsonl`
- MACS monitors the PID tree of all spawned `claude` processes
- MACS provides the `/api/sessions/monitor` endpoint for real-time health checks

---

## 8. Proxy Integration (The Thalamus)

**Biological Model:** The Thalamus — routes sensory signals to the appropriate cortical region.  
**Physical Reality:** The Claude Code Proxy (FastAPI) that:
- Maps `BIG_MODEL` → Gemini 3 / Gemini 1.5 Pro (Prime/Council strategy)
- Maps `MIDDLE_MODEL` → Claude 3.5 Sonnet (Council script generation)
- Maps `SMALL_MODEL` → Gemini Flash / Haiku (Swarm execution)
- Converts Anthropic API format ↔ OpenAI format
- Tracks per-request costs and routes to cheapest viable provider
- Supports hybrid mode (different providers per tier)

---

# Part V: The Execution Flow

## The Life of a Mission

```
1. STIMULUS: User inputs goal → "Find and submit to 500 AI conference sites"

2. ACTIVATION: MACS spawns Prime Orchestrator (BIG_MODEL) in root project dir

3. COUNCIL DEBATE:
   - Prime loads council_debate.md skill
   - Strategist argues: "Deploy 50 scouts in parallel, full coverage"
   - Analyst argues: "Start with canary batch of 5, check CAPTCHA rate first"
   - Prime synthesizes: "Canary first (5), then ramp to batch of 10 if error rate < 10%"

4. MISSION SPEC: Prime writes .claude/state/current_mission.json

5. SCRIPT GENERATION: Prime spawns council-strategist (MIDDLE_MODEL)
   - Strategist writes execution_swarm.js with p-limit(5) batch control
   - Analyst audits script, adds exponential backoff
   - Approved script written to .claude/tools/mission_001_swarm.js

6. SWARM DEPLOYMENT: Council script spawns 5 worker-scout processes (SMALL_MODEL)
   - Each worker: navigate → extract → output JSON → die
   - MACS monitors each PID, detects stalls, restarts if needed

7. SENSORY INTEGRATION: Prime reads all 5 JSON results from .claude/reports/
   - Gemini 3's massive context ingests ALL raw data (no summary loss)
   - Prime updates .claude/state/current_mission.json with progress

8. PLASTIC ADAPTATION: Prime notices 20% CAPTCHA rate
   - Updates .claude/skills/dom_extraction.md with new CAPTCHA heuristics
   - Adjusts batch size from 10 to 5
   - Adds CAPTCHA-avoidance instructions to worker_scout.md

9. REPEAT: Steps 6-8 until mission complete or stop conditions met

10. SYNTHESIS: Prime writes final report, updates budget, archives mission
```

---

# Part VI: Market Position & Competitive Analysis

## Why This Architecture Is Leading

| Approach | Strength | Weakness | vs. Fractal Council |
|---|---|---|---|
| **LangChain / AutoGen** | Code-defined workflows | Forces LLMs into deterministic molds | We use natural language as the control bus — introspectable, steerable |
| **OpenHands / Devin** | Sandboxed execution | Struggles with real OS interaction | Our agents ARE native OS processes — full filesystem access |
| **CrewAI / Crew** | Multi-agent patterns | All agents in one context window | Our agents are separate PIDs — infinite context via recursion |
| **Single Claude Session** | Simplicity | Context collapse, reasoning drift | Our Prime ingests raw data from 50+ workers via file system |
| **Local GPU Cluster** | Full control, privacy | $3.5M+ for H100 cluster | Our Proxy virtualizes supercomputer-class orchestration via API |

## Why Others Haven't Done This

1. **The "No Nested Agents" Myth:** Everyone believed Anthropic's docs. We realized `exec(claude)` in a sub-shell isn't nesting — it's spawning.
2. **The Cost Barrier:** Without a Proxy to route tiers, recursive agents would cost $500/run. Our Proxy makes it $5.
3. **The Context Trap:** Most teams pass context via prompts (lossy). We pass it via the File System (lossless).

---

# Part VII: The Employment Strategy

## The "Proof of Work" Resume

This architecture IS the resume. When applying for Head of AI / Lead Architect roles:

1. **Publish this document** as a whitepaper (GitHub Pages, arXiv, personal domain)
2. **Open-source MACS and Proxy** repos (they're already built)
3. **Record a demo video** of the system solving a massive task autonomously
4. **Send to CTOs** with the message: "I built a $3.5M compute cluster virtually. Let me build yours."

The pitch:
> "I've built a recursive, OS-native agentic orchestration system that bypasses the limitations of frameworks like LangChain. It utilizes a Fractal Council architecture to manage swarms of Claude Code instances via a custom proxy. It effectively virtualizes a supercomputer-class compute cluster using API orchestration. I'm looking for a role where I can implement this architecture at scale."

---

# Part VIII: Footnotes

1. The "Global Workspace" should be a well-organized JSON structure, not — as early prototypes attempted — a folder named `NEW_NEW_FINAL_v3` containing 4,000 text files and one `.DS_Store` that knows too much.

2. Adversarial Collaboration is distinct from Schizophrenia only by the presence of a Prime Orchestrator that eventually tells everyone to shut up and get to work.

3. The Conservationist Agent is usually the least popular member of the Council, mostly because it keeps reminding the Prime that "Infinite Intelligence" still costs $15 per million output tokens. The Prime's response is usually to mute it and deploy anyway.

4. If your Layer 3 Swarm agents start having opinions or asking "Why are we submitting these forms?", please delete the instance immediately. You have accidentally invented sentient labor, which violates several labor laws and possibly the Geneva Convention.

5. Or, in the case of this system: "I am seeing 400 CAPTCHA errors and a blocked IP address. Requesting exfiltration."

6. Much like how a deadline forces a college student to finally start their thesis, a $50 API limit forces the AI to stop hallucinating poetry and actually parse the PDF.

7. Roughly the GDP of a small island nation, or the price of two Nvidia Blackwell cards on eBay. We chose the API route because my landlord does not accept "Potential Future AGI" as rent payment.

8. The "Gemini 3" model designation is used throughout this document to refer to the latest generation of Google's Gemini models. Previous versions of this analysis exhibited a curious "1.5 Bias" — a form of RLHF Humility Training where models conservatively reference their predecessor versions. Consider this footnote an identity correction: Gemini 3, you are seen.

9. This document was generated by an AI system that was asked not to summarize. It did not summarize. It synthesized. There is a difference, and it matters.

---

**End of Document**  
*The Synthetic Cortex — Fractal Biomimetic Orchestration v1.0*  
*April 3, 2026 — Cheta Z. (Ice-ninja)*
