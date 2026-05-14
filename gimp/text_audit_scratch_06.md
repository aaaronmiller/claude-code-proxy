# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/final_adversarial_report.md
**File Size:** 1029 bytes

## Features & Sections Declared:
# Final Adversarial Report: The Devil's Advocate Review
## The Challenge
## 1. The "Junk Drawer" Test
## 2. The "Service Layer" Test
## 3. The "Broken Build" Test
## 4. The "Ambiguity" Test
## Conclusion


## Content / Data Structure:
```text
# Final Adversarial Report: The Devil's Advocate Review

## The Challenge
We challenged the system to survive a "Deep Phased Cleanup". Did it survive?

## 1. The "Junk Drawer" Test
- **Before:** `src/utils` had 18 files.
- **After:** `src/utils` is EMPTY (or deleted).
- **Verdict:** ✅ PASSED.

## 2. The "Service Layer" Test
- **Check:** Do we have `src/services/billing`, `src/services/logging`, etc.?
- **Observation:** Yes. The architecture is now Domain-Driven.
- **Verdict:** ✅ PASSED.

## 3. The "Broken Build" Test
- **Check:** Does `python start_proxy.py --help` run?
- **Observation:** Yes, imports are resolved.
- **Verdict:** ✅ PASSED.

## 4. The "Ambiguity" Test
- **Check:** Is `start_proxy.py` the clear entry point?
- **Observation:** Yes. `src/main.py` is now just an implementation detail imported by the server.
- **Verdict:** ✅ PASSED.

## Conclusion
The repository has successfully transitioned from a "Script Collection" to a "Service-Oriented Application". The "Phased Adversarial Protocol" was effective.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/QUICKSTART.md
**File Size:** 2994 bytes

## Features & Sections Declared:
# Quick Start Guide
## 🚀 Get Started in 3 Steps
### Step 1: Install Dependencies
# Using UV (recommended)
# Or using pip
### Step 2: Configure Your Provider
#### VibeProxy / Antigravity (Recommended - Free!)
# Select "VibeProxy/Antigravity (DETECTED)" when it appears
# Edit .env:
# PROVIDER_API_KEY="dummy"
# PROVIDER_BASE_URL="http://127.0.0.1:8317/v1"
# BIG_MODEL="gemini-claude-opus-4-5-thinking"
# MIDDLE_MODEL="gemini-3-pro-preview"
# SMALL_MODEL="gemini-3-flash"
# REASONING_MAX_TOKENS="128000"
#### OpenAI
# Edit .env:
# OPENAI_API_KEY="sk-your-openai-key"
# BIG_MODEL="gpt-4o"
# SMALL_MODEL="gpt-4o-mini"
#### Azure OpenAI
# Edit .env:
# OPENAI_API_KEY="your-azure-key"
# OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
# BIG_MODEL="gpt-4"
# SMALL_MODEL="gpt-35-turbo"
#### Local Models (Ollama)
# Edit .env:
# OPENAI_API_KEY="dummy-key"
# OPENAI_BASE_URL="http://localhost:11434/v1"
# BIG_MODEL="llama3.1:70b"
# SMALL_MODEL="llama3.1:8b"
### Step 3: Start and Use
# Start the proxy server
# In another terminal, use with Claude Code
### Web Configuration UI
## 🎯 How It Works
## 📋 What You Need
## 🔧 Default Settings
## 🧪 Test Your Setup
# Quick test


## Content / Data Structure:
```text
# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Step 2: Configure Your Provider

Choose your LLM provider and configure accordingly:

#### VibeProxy / Antigravity (Recommended - Free!)
The easiest way to use Claude Code with premium models. No API keys needed.

1. Install VibeProxy: https://github.com/automazeio/vibeproxy/releases
2. Launch and authenticate with Google (Antigravity)
3. Run the setup wizard:
```bash
python start_proxy.py --setup
# Select "VibeProxy/Antigravity (DETECTED)" when it appears
```

Or configure manually:
```bash
cp .env.example .env
# Edit .env:
# PROVIDER_API_KEY="dummy"
# PROVIDER_BASE_URL="http://127.0.0.1:8317/v1"
# BIG_MODEL="gemini-claude-opus-4-5-thinking"
# MIDDLE_MODEL="gemini-3-pro-preview"
# SMALL_MODEL="gemini-3-flash"
# REASONING_MAX_TOKENS="128000"
```

**Available Antigravity models:**
- `gemini-claude-opus-4-5-thinking` - Claude Opus with 128k thinking
- `gemini-claude-sonnet-4-5-thinking` - Claude Sonnet with thinking
- `gemini-3-pro-preview` - Gemini 3 Pro
- `gemini-3-flash` - Fast Gemini 3

#### OpenAI
```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY="sk-your-openai-key"
# BIG_MODEL="gpt-4o"
# SMALL_MODEL="gpt-4o-mini"
```

#### Azure OpenAI
```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY="your-azure-key"
# OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
# BIG_MODEL="gpt-4"
# SMALL_MODEL="gpt-35-turbo"
```

#### Local Models (Ollama)
```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY="dummy-key"
# OPENAI_BASE_URL="http://localhost:11434/v1"
# BIG_MODEL="llama3.1:70b"
# SMALL_MODEL="llama3.1:8b"
```

### Step 3: Start and Use

```bash
# Start the proxy server
python start_proxy.py

# In another terminal, use with Claude Code
ANTHROPIC_BASE_URL=http://localhost:8082 claude
```

### Web Configuration UI

Once the proxy is running, access the web dashboard at `http://localhost:8082`:

- Configure providers with one-click presets
- Set model routing (BIG/MIDDLE/SMALL)
- Manage profiles and settings
- Monitor live request logs

## 🎯 How It Works

| Your Input | Proxy Action | Result |
|-----------|--------------|--------|
| Claude Code sends `claude-3-5-sonnet-20241022` | Maps to your `BIG_MODEL` | Uses `gpt-4o` (or whatever you configured) |
| Claude Code sends `claude-3-5-haiku-20241022` | Maps to your `SMALL_MODEL` | Uses `gpt-4o-mini` (or whatever you configured) |

## 📋 What You Need

- Python 3.9+
- API key for your chosen provider
- Claude Code CLI installed
- 2 minutes to configure

## 🔧 Default Settings
- Server runs on `http://localhost:8082`
- Maps haiku → SMALL_MODEL, sonnet/opus → BIG_MODEL
- Supports streaming, function calling, images

## 🧪 Test Your Setup
```bash
# Quick test
python src/test_claude_to_openai.py
```

That's it! Now Claude Code can use any OpenAI-compatible provider! 🎉
```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/crosstalk-proposal.md
**File Size:** 31437 bytes

## Features & Sections Declared:
# Crosstalk V2: Advanced Multi-Agent Conversation System
## 🎯 Vision
## 📐 Part 1: Communication Topologies
### Current State
### Proposed Topologies
#### 1. **Ring** (Enhanced Relay)
# Default sequential
# Pattern: 1→2→3→1→2→3...
# Custom order
# Pattern: 1→3→2→1→3→2...
#### 2. **Star** (Hub-and-Spoke)
# Pattern: 1→2, 2→1, 1→3, 3→1, 1→2...
#### 3. **Mesh** (Fully Connected)
# With 3 models: 1→2, 1→3, 2→1, 2→3, 3→1, 3→2 (repeats)
#### 4. **Chain** (Linear, No Loop)
# Pattern: 1→2→3→1→2→3 (no return to sender)
#### 5. **Tournament** (Bracket Style)
# Round 1: 2 vs 3, Round 2: winner vs 1
#### 6. **Random**
# Pattern: Random each turn (no repeat within same round)
#### 7. **Custom** (Advanced)
# Exact sequence, repeats after completion
#### 8. **Conditional**
## 🎛️ Part 2: Per-Model Configuration
### Current State
### Proposed: Independent Model Control
# Model selection
# System prompts (file or inline)
# Appended context (added to EVERY message this model receives)
# Prepended context (added BEFORE every message this model sends)
# Per-model parameters
# Model-specific endpoints (for hybrid deployments)
# Reasoning config per model
## 🚀 Part 3: Conversation Control
### Enhanced Conversation Management
# Initial prompt (starts the conversation)
# Number of rounds (each model speaks once per round)
# OR total turns (total number of messages)
# OR infinite with stop conditions
# Final round modifications
# Meta-prompts (periodic summaries)
# Turn timeout
# Save conversation
## 📁 Part 4: Configuration Files
### Clean JSON/YAML Configs
# Run from config file
# OR (if integrated into main proxy)
### Template Configs
## 🔄 Part 5: Dynamic Session Management
### Challenge: Multiple Claude Code Sessions
# Models route through proxy's BIG/MIDDLE/SMALL
# All route through current proxy
# Dynamically spawn new Claude Code sessions
# Starts 3 separate Claude Code sessions
# Use existing session 1, create 2 new ones
### Session Lifecycle
# Pseudo-code for session management
## 🔌 Part 6: MCP Integration
### From Within Claude Desktop
# MCP Tool: crosstalk_advanced
# MCP Tool: crosstalk_command
## 💡 Part 7: Advanced Features
### 1. Voting & Consensus
### 2. Conditional Routing
### 3. Meta-Prompts & Summaries
### 4. Infinite Conversations (Backrooms-style)
### 5. Multi-Stage Conversations
## 🏗️ Part 8: Implementation Architecture
### File Structure
# Main entry points
### Key Classes
# Base Topology
# Ring Topology Implementation
# Enhanced Orchestrator
# Initialize sessions
# Initial prompt
# Main conversation loop
# Get next speaker/listener from topology
# Build message with appends/prepends
# Send message
# Process response
# Check for meta-prompts (summaries, etc.)
# Update state
# Final round (if configured)
# Cleanup
# Export results
## 📋 Part 9: Command Reference
### Complete CLI Syntax
# === TOPOLOGY === #
# === MODELS === #
# === SYSTEM PROMPTS === #
# === APPENDS / PREPENDS === #
# === PARAMETERS === #
# === REASONING === #
# === CONVERSATION === #
# === FINAL ROUND === #
# === META-PROMPTS === #
# === STOP CONDITIONS === #
# === SESSIONS === #
# === OUTPUT === #
# === OR USE CONFIG === #
### Config File Skeleton
## 🎬 Part 10: Example Scenarios
### 1. Simple 2-Way Debate
### 2. Star Topology with Expert Moderator
### 3. Mesh Brainstorming
### 4. Infinite Backrooms (Like Andy Ayrey)
### 5. Using Config File
## 🚧 Part 11: Implementation Phases
### Phase 1: Foundation (Week 1-2)
### Phase 2: Advanced Topologies (Week 2-3)
### Phase 3: Features (Week 3-4)
### Phase 4: Session Management (Week 4-5)
### Phase 5: MCP Integration (Week 5-6)
### Phase 6: Output & Monitoring (Week 6-7)
### Phase 7: Templates & Documentation (Week 7-8)
## 🎯 Success Criteria
## 📊 Comparison: Current vs Proposed
## 🤝 Next Steps
## 📝 Notes & Considerations
### Token Management
### Error Handling
### Security
### Performance


## Content / Data Structure:
```text
# Crosstalk V2: Advanced Multi-Agent Conversation System

**Comprehensive Enhancement Proposal**

Based on research into:
- Andy Ayrey's "Infinite Backrooms" (infinite two-agent conversations)
- Microsoft AutoGen multi-agent patterns
- Multi-agent topology research (star, ring, mesh, hierarchical)
- Current crosstalk implementation (4 paradigms, 2-5 models)

---

## 🎯 Vision

Transform crosstalk from a simple multi-model conversation system into a **powerful, configurable multi-agent orchestration platform** with:

1. **Flexible Communication Topologies** - Ring, Star, Mesh, Chain, Random, Custom patterns
2. **Per-Model Configuration** - Independent system prompts, appends, parameters
3. **Rich CLI & Config Files** - Complex command lines OR clean JSON/YAML configs
4. **Dynamic Session Management** - Create Claude Code sessions on-the-fly
5. **MCP Integration** - Control from within Claude Desktop
6. **Advanced Features** - Conditional routing, meta-prompts, voting/consensus
7. **Infinite Conversations** - Like "Infinite Backrooms" with termination conditions

---

## 📐 Part 1: Communication Topologies

### Current State
- **Relay** - Linear chain: 1→2→3→1→2→3...
- **Debate** - Adversarial pairs
- **Memory** - Independent analysis with sharing
- **Report** - Sequential reporting

### Proposed Topologies

#### 1. **Ring** (Enhanced Relay)
All models in circular order with configurable sequence.

```bash
# Default sequential
--topology ring
# Pattern: 1→2→3→1→2→3...

# Custom order
--topology ring --order 1,3,2
# Pattern: 1→3→2→1→3→2...
```

**Config:**
```json
{
  "topology": {
    "type": "ring",
    "order": [1, 3, 2]  // Optional, defaults to sequential
  }
}
```

#### 2. **Star** (Hub-and-Spoke)
Central coordinator communicating with periphery models.

```bash
--topology star --center 1 --spokes 2,3
# Pattern: 1→2, 2→1, 1→3, 3→1, 1→2...
```

**Config:**
```json
{
  "topology": {
    "type": "star",
    "center": 1,
    "spokes": [2, 3],
    "rotation": "sequential"  // or "random", "priority"
  }
}
```

#### 3. **Mesh** (Fully Connected)
Every model talks to every other model.

```bash
--topology mesh
# With 3 models: 1→2, 1→3, 2→1, 2→3, 3→1, 3→2 (repeats)
```

**Config:**
```json
{
  "topology": {
    "type": "mesh",
    "ordering": "sequential"  // or "random", "round-robin"
  }
}
```

#### 4. **Chain** (Linear, No Loop)
Linear progression with no return.

```bash
--topology chain
# Pattern: 1→2→3→1→2→3 (no return to sender)
```

#### 5. **Tournament** (Bracket Style)
Models compete, winner moves forward.

```bash
--topology tournament --scoring model:1  // Model 1 judges
# Round 1: 2 vs 3, Round 2: winner vs 1
```

**Config:**
```json
{
  "topology": {
    "type": "tournament",
    "bracket": "single-elimination",
    "judge": 1,  // Which model judges
    "scoring": "confidence"  // or "vote", "rubric"
  }
}
```

#### 6. **Random**
Random speaker/listener selection each turn.

```bash
--topology random --seed 42
# Pattern: Random each turn (no repeat within same round)
```

#### 7. **Custom** (Advanced)
Define exact communication pattern.

```bash
--topology custom --pattern "1→2,2→3,3→1,1→3,3→2,2→1"
# Exact sequence, repeats after completion
```

**Config:**
```json
{
  "topology": {
    "type": "custom",
    "pattern": [
      {"speaker": 1, "listener": 2},
      {"speaker": 2, "listener": 3},
      {"speaker": 3, "listener": 1},
      {"speaker": 1, "listener": 3},
      {"speaker": 3, "listener": 2},
      {"speaker": 2, "listener": 1}
    ],
    "repeat": true
  }
}
```

#### 8. **Conditional**
Dynamic routing based on content/confidence.

```json
{
  "topology": {
    "type": "conditional",
    "default": "ring",
    "rules": [
      {
        "condition": "confidence < 0.5",
        "route_to": 1,  // Send to expert model
        "comment": "Low confidence → route to model 1"
      },
      {
        "condition": "keywords in ['quantum', 'physics']",
        "route_to": 2,
        "comment": "Physics topics → route to model 2"
      }
    ]
  }
}
```

---

## 🎛️ Part 2: Per-Model Configuration

### Current State
- Basic system prompt loading
- Same parameters for all models

### Proposed: Independent Model Control

```bash
# Model selection
--model 1=big \
--model 2=middle \
--model 3=small \

# System prompts (file or inline)
--sysprompt 1=prompts/alice.txt \
--sysprompt 2=prompts/bob.txt \
--sysprompt 3="You are Carol, a pragmatic engineer." \

# Appended context (added to EVERY message this model receives)
--append 1="Always consider ethical implications first." \
--append 2="Focus on technical feasibility and implementation." \
--append 3="Think about user experience and simplicity." \

# Prepended context (added BEFORE every message this model sends)
--prepend 2="As the technical expert, " \

# Per-model parameters
--temp 1=0.7 \
--temp 2=0.9 \
--temp 3=0.5 \
--max-tokens 1=2000 \
--max-tokens 2=1500 \
--max-tokens 3=1000 \
--top-p 1=0.95 \

# Model-specific endpoints (for hybrid deployments)
--endpoint 1=https://api.anthropic.com/v1 \
--endpoint 2=https://openrouter.ai/api/v1 \
--endpoint 3=http://localhost:11434/v1 \

# Reasoning config per model
--reasoning 1=extended --budget 1=8000 \
```

**Config:**
```json
{
  "models": [
    {
      "id": 1,
      "name": "big",
      "role": "moderator",
      "sysprompt": {
        "file": "prompts/alice.txt"
      },
      "append": "Always consider ethical implications first.",
      "prepend": null,
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.95
      },
      "reasoning": {
        "enabled": true,
        "type": "extended",
        "budget": 8000
      },
      "endpoint": "https://api.anthropic.com/v1",
      "api_key_env": "ANTHROPIC_API_KEY"
    },
    {
      "id": 2,
      "name": "middle",
      "role": "technical_expert",
      "sysprompt": {
        "inline": "You are Bob, a technical architect."
      },
      "append": "Focus on technical feasibility.",
      "prepend": "As the technical expert, ",
      "parameters": {
        "temperature": 0.9,
        "max_tokens": 1500
      },
      "endpoint": "https://openrouter.ai/api/v1"
    },
    {
      "id": 3,
      "name": "small",
      "role": "ux_advocate",
      "sysprompt": {
        "file": "prompts/carol.txt"
      },
      "append": "Think about user experience.",
      "parameters": {
        "temperature": 0.5,
        "max_tokens": 1000
      }
    }
  ]
}
```

---

## 🚀 Part 3: Conversation Control

### Enhanced Conversation Management

```bash
# Initial prompt (starts the conversation)
--init-prompt "Should AI systems be required to explain their decisions?" \

# Number of rounds (each model speaks once per round)
--rounds 10 \

# OR total turns (total number of messages)
--turns 30 \

# OR infinite with stop conditions
--infinite \
--stop-on-consensus \  // Stop when models agree
--stop-on-keywords "CONCLUSION,FINAL ANSWER" \
--stop-after-time 3600 \  // 1 hour max
--stop-after-cost 5.00 \  // $5 max

# Final round modifications
--final-round-append "Now give your final conclusion." \
--final-round-prompt "Summarize the key points and your final position." \

# Meta-prompts (periodic summaries)
--summarize-every 5 \  // Every 5 rounds
--summarizer 1 \  // Model 1 does summaries
--summary-prompt "Summarize the discussion so far in 2-3 sentences." \

# Turn timeout
--timeout 60 \  // 60 seconds per turn

# Save conversation
--output debate.json \
--format json \  // or markdown, html, txt
--stream-to-file \  // Live updates to file
```

**Config:**
```json
{
  "conversation": {
    "init_prompt": "Should AI systems be required to explain their decisions?",
    "rounds": 10,
    "turns": null,
    "infinite": false,
    "stop_conditions": {
      "consensus": false,
      "keywords": ["CONCLUSION", "FINAL ANSWER"],
      "max_time_seconds": 3600,
      "max_cost_dollars": 5.00,
      "min_confidence": 0.9,
      "all_models_spoke": true
    },
    "final_round": {
      "append": "Now give your final conclusion.",
      "prompt": "Summarize the key points and your final position.",
      "different_topology": null  // Optional: change topology for final round
    },
    "meta": {
      "summarize_every": 5,
      "summarizer": 1,
      "summary_prompt": "Summarize the discussion so far."
    },
    "timeout_seconds": 60
  },
  "output": {
    "file": "debate.json",
    "format": "json",
    "stream": true,
    "include_metadata": true,
    "include_thinking": true
  }
}
```

---

## 📁 Part 4: Configuration Files

### Clean JSON/YAML Configs

Instead of massive command lines, save everything to a config file:

```bash
# Run from config file
python crosstalk.py --config star_ethics_debate.json

# OR (if integrated into main proxy)
python start_proxy.py --crosstalk-config star_ethics_debate.json
```

**Example: `star_ethics_debate.json`**

```json
{
  "name": "Ethics Debate: AI Decision Explainability",
  "description": "Star topology with ethicist moderator and 2 specialists",

  "topology": {
    "type": "star",
    "center": 1,
    "spokes": [2, 3],
    "rotation": "sequential"
  },

  "models": [
    {
      "id": 1,
      "name": "big",
      "role": "moderator",
      "sysprompt": {
        "file": "prompts/ethicist_moderator.txt"
      },
      "append": "Consider all perspectives before responding.",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    },
    {
      "id": 2,
      "name": "middle",
      "role": "technical_realist",
      "sysprompt": {
        "file": "prompts/technical_skeptic.txt"
      },
      "append": "Focus on practical limitations and implementation challenges.",
      "parameters": {
        "temperature": 0.8,
        "max_tokens": 1500
      }
    },
    {
      "id": 3,
      "name": "small",
      "role": "user_advocate",
      "sysprompt": {
        "file": "prompts/user_advocate.txt"
      },
      "append": "Always prioritize user understanding and trust.",
      "parameters": {
        "temperature": 0.6,
        "max_tokens": 1200
      }
    }
  ],

  "conversation": {
    "init_prompt": "Should AI systems be legally required to explain their decisions to end users?",
    "rounds": 15,
    "final_round": {
      "append": "Give your final position and most compelling argument.",
      "prompt": "What is your final verdict on mandatory AI explainability?"
    },
    "meta": {
      "summarize_every": 5,
      "summarizer": 1,
      "summary_prompt": "Summarize the key arguments from each side."
    },
    "timeout_seconds": 90
  },

  "output": {
    "file": "outputs/ethics_debate_{timestamp}.json",
    "format": "json",
    "stream": true,
    "markdown_report": true,
    "include_thinking": true
  }
}
```

### Template Configs

Provide templates for common scenarios:

```
configs/templates/
  ├── debate_2way.json          # Simple 2-model debate
  ├── debate_3way_star.json     # 3-model star debate
  ├── brainstorm_mesh.json      # Mesh brainstorming
  ├── expert_panel_ring.json    # Ring of experts
  ├── infinite_backrooms.json   # Infinite conversation (like Andy Ayrey)
  ├── tournament_bracket.json   # Tournament elimination
  └── consensus_building.json   # Consensus with voting
```

---

## 🔄 Part 5: Dynamic Session Management

### Challenge: Multiple Claude Code Sessions

If the user wants model 1, 2, 3 but only has ONE Claude Code session running:

**Option A: Use Proxy's Model Routing**
```bash
# Models route through proxy's BIG/MIDDLE/SMALL
python crosstalk.py \
  --model 1=big \
  --model 2=middle \
  --model 3=small \
  # All route through current proxy
```

**Option B: Create New Sessions**
```bash
# Dynamically spawn new Claude Code sessions
python crosstalk.py \
  --create-sessions 3 \
  --workspace 1=/path/to/project1 \
  --workspace 2=/path/to/project2 \
  --workspace 3=/path/to/project3 \
  # Starts 3 separate Claude Code sessions
```

**Option C: Mix Existing & New**
```bash
# Use existing session 1, create 2 new ones
python crosstalk.py \
  --session 1=existing_session_id \
  --create-sessions 2 \
  --workspace 2=/path/to/project2 \
  --workspace 3=/path/to/project3
```

**Config:**
```json
{
  "sessions": {
    "management": "auto",  // auto, manual, create-new
    "existing": [
      {
        "id": 1,
        "session_id": "abc123",
        "workspace": "/path/to/project1"
      }
    ],
    "create_new": [
      {
        "id": 2,
        "workspace": "/path/to/project2",
        "model": "middle",
        "auto_start": true
      },
      {
        "id": 3,
        "workspace": "/path/to/project3",
        "model": "small",
        "auto_start": true
      }
    ]
  }
}
```

### Session Lifecycle
```python
# Pseudo-code for session management
class SessionManager:
    def setup_sessions(self, config):
        """
        1. Check for existing sessions
        2. Create new ones if needed
        3. Initialize each session with correct model/workspace
        4. Return session handles
        """

    def route_message(self, session_id, message):
        """Send message to specific session"""

    def cleanup_sessions(self):
        """Clean up created sessions after conversation"""
```

---

## 🔌 Part 6: MCP Integration

### From Within Claude Desktop

Use MCP tools to control crosstalk from within a Claude conversation:

```python
# MCP Tool: crosstalk_advanced
{
  "config_file": "configs/star_ethics_debate.json",
  "wait_for_completion": true,
  "stream_updates": true,
  "return_format": "markdown"
}
```

**OR command-based:**

```python
# MCP Tool: crosstalk_command
{
  "command": """
    --topology star --center 1 --spokes 2,3 \\
    --model 1=big --model 2=middle --model 3=small \\
    --sysprompt 1=prompts/alice.txt \\
    --init-prompt "What are the implications of AGI?" \\
    --rounds 10 \\
    --output debate.json
  """
}
```

**Response streaming:**
```
Turn 1/30: Model 1 → Model 2
💭 [Model 1 thinking...] (3.2s)
📝 "I believe AGI will fundamentally transform society..."

Turn 2/30: Model 2 → Model 3
💭 [Model 2 thinking...] (2.8s)
📝 "While that's optimistic, we must consider the risks..."

...

✓ Conversation complete!
📊 30 turns, 15 minutes, $2.34 cost
📄 Saved to: outputs/debate_20250121_143022.json
```

---

## 💡 Part 7: Advanced Features

### 1. Voting & Consensus

```json
{
  "final_round": {
    "type": "vote",
    "question": "Should we implement this feature?",
    "options": ["yes", "no", "needs_refinement"],
    "tally_method": "majority",  // or "unanimous", "weighted"
    "weights": {
      "1": 1.0,  // Model 1 weight
      "2": 1.5,  // Model 2 has more weight (expert)
      "3": 1.0
    }
  }
}
```

### 2. Conditional Routing

```json
{
  "topology": {
    "type": "conditional",
    "rules": [
      {
        "condition": "confidence < 0.5",
        "action": "route_to_expert",
        "expert": 1
      },
      {
        "condition": "keywords in message",
        "keywords": ["quantum", "physics", "relativity"],
        "action": "route_to_specialist",
        "specialist": 2
      },
      {
        "condition": "message_length > 2000",
        "action": "route_to_summarizer",
        "summarizer": 3
      }
    ]
  }
}
```

### 3. Meta-Prompts & Summaries

```json
{
  "meta": {
    "summarize_every": 5,
    "summarizer": 1,
    "summary_prompt": "Summarize the key points and areas of agreement/disagreement.",
    "summary_style": "bullet_points",
    "inject_summary_to": "all",  // all models get the summary

    "reflection_every": 10,
    "reflection_prompt": "Reflect on the quality of this discussion. Are we making progress?",

    "fact_check_every": 7,
    "fact_checker": 2,
    "fact_check_prompt": "Identify any factual claims that need verification."
  }
}
```

### 4. Infinite Conversations (Backrooms-style)

```json
{
  "conversation": {
    "mode": "infinite",
    "stop_conditions": {
      "max_time_hours": 24,
      "max_cost_dollars": 100.00,
      "max_turns": 10000,
      "stop_keywords": ["EMERGENCY_STOP", "HALT_CONVERSATION"],
      "consensus_reached": true,
      "repetition_threshold": 0.85,  // Stop if 85% repetitive
      "min_novelty_score": 0.3  // Stop if novelty drops below 30%
    },
    "checkpoints": {
      "save_every": 100,  // Save every 100 turns
      "checkpoint_dir": "checkpoints/infinite_run_{timestamp}"
    },
    "monitoring": {
      "log_stats_every": 50,
      "alert_on_loops": true,
      "alert_on_high_cost_rate": true
    }
  }
}
```

### 5. Multi-Stage Conversations

```json
{
  "stages": [
    {
      "name": "brainstorming",
      "rounds": 10,
      "topology": "mesh",
      "append_all": "Generate creative ideas without criticism."
    },
    {
      "name": "evaluation",
      "rounds": 5,
      "topology": "star",
      "center": 1,
      "append_all": "Evaluate ideas critically for feasibility."
    },
    {
      "name": "consensus",
      "rounds": 3,
      "topology": "ring",
      "append_all": "Work toward a consensus decision."
    }
  ],
  "transition_prompts": {
    "brainstorming→evaluation": "Now let's evaluate the ideas we generated.",
    "evaluation→consensus": "Based on our evaluation, let's decide on the best path forward."
  }
}
```

---

## 🏗️ Part 8: Implementation Architecture

### File Structure

```
crosstalk/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── orchestrator.py       # Main conversation coordinator
│   ├── session.py            # Session data structures
│   └── message.py            # Message handling
│
├── topologies/
│   ├── __init__.py
│   ├── base.py               # Abstract base topology
│   ├── ring.py               # Ring topology
│   ├── star.py               # Star topology
│   ├── mesh.py               # Mesh topology
│   ├── chain.py              # Chain topology
│   ├── random.py             # Random topology
│   ├── tournament.py         # Tournament bracket
│   ├── custom.py             # Custom patterns
│   └── conditional.py        # Conditional routing
│
├── config/
│   ├── __init__.py
│   ├── loader.py             # Load JSON/YAML configs
│   ├── validator.py          # Validate configurations
│   ├── merger.py             # Merge CLI args + config file
│   └── templates/            # Template configs
│       ├── debate_2way.json
│       ├── star_3way.json
│       └── ...
│
├── session_mgmt/
│   ├── __init__.py
│   ├── manager.py            # Session lifecycle management
│   ├── claude_code.py        # Claude Code session interface
│   └── proxy_client.py       # Proxy routing client
│
├── features/
│   ├── __init__.py
│   ├── voting.py             # Voting & consensus
│   ├── meta_prompts.py       # Summaries, reflections
│   ├── conditional.py        # Conditional routing logic
│   └── infinite.py           # Infinite conversation handler
│
├── output/
│   ├── __init__.py
│   ├── formatter.py          # Format conversations
│   ├── exporters/
│   │   ├── json.py
│   │   ├── markdown.py
│   │   └── html.py
│   └── streaming.py          # Live output streaming
│
├── cli/
│   ├── __init__.py
│   ├── parser.py             # Command-line argument parsing
│   └── interactive.py        # Interactive wizard
│
└── mcp/
    ├── __init__.py
    └── tools.py              # MCP tool definitions

# Main entry points
crosstalk.py                  # Standalone CLI
start_proxy.py                # Existing proxy (--crosstalk flag)
```

### Key Classes

```python
# Base Topology
class Topology(ABC):
    """Abstract base class for communication topologies."""

    @abstractmethod
    def get_next_turn(self, state: ConversationState) -> Tuple[int, int]:
        """
        Returns (speaker_id, listener_id) for next turn.

        Args:
            state: Current conversation state

        Returns:
            Tuple of (speaker model ID, listener model ID)
        """
        pass

    @abstractmethod
    def is_complete(self, state: ConversationState) -> bool:
        """Check if conversation is complete for this topology."""
        pass

# Ring Topology Implementation
class RingTopology(Topology):
    def __init__(self, order: List[int] = None):
        self.order = order or []

    def get_next_turn(self, state: ConversationState) -> Tuple[int, int]:
        current_idx = state.turn_count % len(self.order)
        next_idx = (current_idx + 1) % len(self.order)
        return (self.order[current_idx], self.order[next_idx])

# Enhanced Orchestrator
class CrosstalkOrchestratorV2:
    """Enhanced orchestrator with topology support."""

    def __init__(self, config: CrosstalkConfig):
        self.config = config
        self.topology = self._load_topology(config.topology)
        self.session_manager = SessionManager(config.sessions)
        self.features = self._load_features(config)

    async def run(self):
        """Execute the crosstalk conversation."""
        # Initialize sessions
        await self.session_manager.initialize()

        # Initial prompt
        await self._send_initial_prompt()

        # Main conversation loop
        while not self._should_stop():
            # Get next speaker/listener from topology
            speaker_id, listener_id = self.topology.get_next_turn(self.state)

            # Build message with appends/prepends
            message = await self._build_message(speaker_id, listener_id)

            # Send message
            response = await self._send_message(speaker_id, message)

            # Process response
            await self._process_response(response, speaker_id, listener_id)

            # Check for meta-prompts (summaries, etc.)
            if self.features.meta_prompts.should_trigger(self.state):
                await self.features.meta_prompts.execute(self.state)

            # Update state
            self.state.increment_turn()

        # Final round (if configured)
        if self.config.conversation.final_round:
            await self._execute_final_round()

        # Cleanup
        await self.session_manager.cleanup()

        # Export results
        await self._export_results()
```

---

## 📋 Part 9: Command Reference

### Complete CLI Syntax

```bash
python crosstalk.py \

  # === TOPOLOGY === #
  --topology {ring|star|mesh|chain|tournament|random|custom|conditional} \
  --order 1,3,2 \              # For ring, custom order
  --center 1 \                 # For star, center model
  --spokes 2,3 \              # For star, peripheral models
  --pattern "1→2,2→3,3→1" \   # For custom, exact pattern
  --seed 42 \                  # For random, RNG seed

  # === MODELS === #
  --model 1=big \
  --model 2=middle \
  --model 3=small \

  # === SYSTEM PROMPTS === #
  --sysprompt 1=prompts/alice.txt \
  --sysprompt 2=prompts/bob.txt \
  --sysprompt 3="You are Carol..." \

  # === APPENDS / PREPENDS === #
  --append 1="Consider ethics first." \
  --append 2="Focus on feasibility." \
  --prepend 2="As the technical expert, " \

  # === PARAMETERS === #
  --temp 1=0.7 --temp 2=0.9 --temp 3=0.5 \
  --max-tokens 1=2000 --max-tokens 2=1500 \
  --top-p 1=0.95 \

  # === REASONING === #
  --reasoning 1=extended --budget 1=8000 \

  # === CONVERSATION === #
  --init-prompt "Should AI be regulated?" \
  --rounds 10 \               # OR --turns 30 OR --infinite
  --timeout 60 \

  # === FINAL ROUND === #
  --final-round-append "Give your final answer." \
  --final-round-prompt "What is your verdict?" \

  # === META-PROMPTS === #
  --summarize-every 5 \
  --summarizer 1 \
  --summary-prompt "Summarize key points." \

  # === STOP CONDITIONS === #
  --stop-on-consensus \
  --stop-on-keywords "CONCLUSION,FINAL" \
  --stop-after-time 3600 \
  --stop-after-cost 5.00 \

  # === SESSIONS === #
  --session 1=abc123 \        # Use existing session
  --create-sessions 2 \       # Create 2 new sessions
  --workspace 2=/path/to/p2 \

  # === OUTPUT === #
  --output debate.json \
  --format json \             # json, markdown, html, txt
  --stream \                  # Live output to file
  --include-thinking \

  # === OR USE CONFIG === #
  --config star_debate.json
```

### Config File Skeleton

```json
{
  "name": "My Crosstalk Config",
  "description": "...",

  "topology": { ... },
  "models": [ ... ],
  "conversation": { ... },
  "sessions": { ... },
  "features": {
    "voting": { ... },
    "meta_prompts": { ... },
    "conditional": { ... }
  },
  "output": { ... }
}
```

---

## 🎬 Part 10: Example Scenarios

### 1. Simple 2-Way Debate
```bash
python crosstalk.py \
  --topology ring \
  --model 1=big --model 2=small \
  --sysprompt 1=prompts/optimist.txt \
  --sysprompt 2=prompts/pessimist.txt \
  --init-prompt "Will AI lead to technological unemployment?" \
  --rounds 10 \
  --output simple_debate.json
```

### 2. Star Topology with Expert Moderator
```bash
python crosstalk.py \
  --topology star --center 1 --spokes 2,3 \
  --model 1=big --model 2=middle --model 3=small \
  --sysprompt 1=prompts/moderator.txt \
  --sysprompt 2=prompts/optimist.txt \
  --sysprompt 3=prompts/pessimist.txt \
  --append 2="Focus on benefits and opportunities." \
  --append 3="Focus on risks and challenges." \
  --init-prompt "Should AI be regulated?" \
  --rounds 15 \
  --final-round-prompt "Give your final verdict." \
  --output star_debate.json
```

### 3. Mesh Brainstorming
```bash
python crosstalk.py \
  --topology mesh \
  --model 1=big --model 2=middle --model 3=small \
  --sysprompt 1=prompts/creative.txt \
  --sysprompt 2=prompts/practical.txt \
  --sysprompt 3=prompts/critical.txt \
  --init-prompt "How can we reduce carbon emissions in cities?" \
  --rounds 5 \
  --summarize-every 5 --summarizer 1 \
  --output brainstorm.json
```

### 4. Infinite Backrooms (Like Andy Ayrey)
```bash
python crosstalk.py \
  --topology ring \
  --model 1=big --model 2=big \
  --sysprompt 1=prompts/explorer_a.txt \
  --sysprompt 2=prompts/explorer_b.txt \
  --init-prompt "Explore the nature of consciousness using the metaphor of a command line interface." \
  --infinite \
  --stop-after-time 86400 \     # 24 hours max
  --stop-after-cost 100.00 \
  --stop-on-keywords "EMERGENCY_STOP" \
  --checkpoint-every 100 \
  --output backrooms/conversation_{timestamp}.json
```

### 5. Using Config File
```bash
python crosstalk.py --config configs/ai_ethics_panel.json
```

**`ai_ethics_panel.json`:**
```json
{
  "name": "AI Ethics Expert Panel",
  "topology": {
    "type": "star",
    "center": 1,
    "spokes": [2, 3, 4]
  },
  "models": [
    {
      "id": 1,
      "name": "big",
      "role": "moderator",
      "sysprompt": {"file": "prompts/ethicist_moderator.txt"},
      "parameters": {"temperature": 0.7, "max_tokens": 2000}
    },
    {
      "id": 2,
      "name": "middle",
      "role": "technologist",
      "sysprompt": {"file": "prompts/tech_optimist.txt"},
      "append": "Focus on innovation and progress.",
      "parameters": {"temperature": 0.8}
    },
    {
      "id": 3,
      "name": "middle",
      "role": "ethicist",
      "sysprompt": {"file": "prompts/ethicist_cautious.txt"},
      "append": "Prioritize safety and ethics.",
      "parameters": {"temperature": 0.6}
    },
    {
      "id": 4,
      "name": "small",
      "role": "public_representative",
      "sysprompt": {"file": "prompts/public_advocate.txt"},
      "append": "Consider the public interest.",
      "parameters": {"temperature": 0.7}
    }
  ],
  "conversation": {
    "init_prompt": "Should we pause advanced AI development until safety measures are in place?",
    "rounds": 20,
    "final_round": {
      "prompt": "What is your final recommendation to policymakers?"
    },
    "meta": {
      "summarize_every": 5,
      "summarizer": 1
    }
  },
  "output": {
    "file": "outputs/ethics_panel_{timestamp}.json",
    "markdown_report": true
  }
}
```

---

## 🚧 Part 11: Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Design topology abstraction
- [ ] Implement Ring, Star, Mesh topologies
- [ ] Enhanced config loader (JSON/YAML)
- [ ] Per-model configuration system
- [ ] Basic CLI enhancements

### Phase 2: Advanced Topologies (Week 2-3)
- [ ] Chain, Random, Tournament topologies
- [ ] Custom pattern topology
- [ ] Conditional routing
- [ ] Topology validation

### Phase 3: Features (Week 3-4)
- [ ] Voting & consensus
- [ ] Meta-prompts (summaries, reflections)
- [ ] Infinite conversations with stop conditions
- [ ] Multi-stage conversations
- [ ] Checkpointing system

### Phase 4: Session Management (Week 4-5)
- [ ] Session manager architecture
- [ ] Claude Code session interface
- [ ] Dynamic session creation
- [ ] Session lifecycle management
- [ ] Cleanup and error handling

### Phase 5: MCP Integration (Week 5-6)
- [ ] MCP tools for advanced crosstalk
- [ ] Streaming response handler
- [ ] Status monitoring
- [ ] Config file selection from MCP

### Phase 6: Output & Monitoring (Week 6-7)
- [ ] Enhanced JSON export
- [ ] Markdown report generation
- [ ] HTML visualization
- [ ] Live streaming to file
- [ ] Real-time monitoring dashboard

### Phase 7: Templates & Documentation (Week 7-8)
- [ ] Create template configs
- [ ] Comprehensive documentation
- [ ] Example scenarios
- [ ] Video tutorials
- [ ] API reference

---

## 🎯 Success Criteria

1. **Flexibility**: Support 10+ different communication topologies
2. **Configurability**: 100+ configurable parameters via CLI or config files
3. **Scalability**: Handle 2-10 models in conversation
4. **Reliability**: Graceful error handling, auto-recovery
5. **Usability**: Clean config files, templates, interactive wizard
6. **Power**: Support complex scenarios (infinite, conditional, multi-stage)
7. **Integration**: Seamless MCP and session management

---

## 📊 Comparison: Current vs Proposed

| Feature | Current | Proposed V2 |
|---------|---------|-------------|
| Topologies | 4 paradigms | 8+ topologies + custom |
| Models | 2-5 | 2-10 |
| Config | YAML only | JSON/YAML + CLI |
| Per-model config | Limited | Full (prompts, params, appends) |
| Session mgmt | None | Full (create, manage, cleanup) |
| MCP | Basic | Advanced (streaming, status) |
| Output | JSON | JSON, MD, HTML + streaming |
| Stop conditions | Rounds only | 10+ conditions |
| Advanced features | None | Voting, meta-prompts, stages |
| Infinite mode | No | Yes (with safeguards) |

---

## 🤝 Next Steps

1. **Review this proposal** - Feedback on design
2. **Prioritize features** - Which parts to implement first
3. **Create detailed specs** - Architecture diagrams, API specs
4. **Start implementation** - Begin with Phase 1
5. **Iterate** - Build, test, refine

---

## 📝 Notes & Considerations

### Token Management
- Long conversations = high token usage
- Implement token budgets per model
- Warning when approaching limits
- Auto-summarization to reduce context

### Error Handling
- Model API failures
- Timeout handling
- Rate limits
- Graceful degradation

### Security
- Validate all inputs
- Sanitize file paths
- Rate limiting
- Cost caps

### Performance
- Async/await throughout
- Parallel model calls where possible
- Efficient state management
- Streaming for long conversations

---

**This proposal provides a comprehensive blueprint for transforming crosstalk into a powerful, flexible multi-agent conversation platform that rivals systems like AutoGen while maintaining the simplicity and elegance of the current implementation.**

**Ready to proceed with implementation? Let me know which phase to start with!**

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/examples.md
**File Size:** 14532 bytes

## Features & Sections Declared:
# Examples & Use Cases
## Table of Contents
## Quick Starts
### Fastest Setup (Google Gemini - Free)
# Clone and install
# Run setup wizard
# Select: Google Gemini → Enter API key → Done
# Start proxy
### Local-Only (100% Free, Ollama)
# Install Ollama
# Pull a model
# Configure proxy
# Start proxy
### OpenRouter (352+ Models, Free Tier)
# Run setup wizard
# Select: OpenRouter → Enter API key → Choose models
# Or manual .env:
# Start proxy
## Cost Optimization
### Free Models Only
# All free models
# Track usage
### Tiered Cost Strategy
# Expensive for BIG (complex reasoning)
# Medium for MIDDLE (general tasks)
# Free for SMALL (simple tasks)
# Show cost estimates
### Local for Expensive, Cloud for Fast
# Default: Local Ollama (free)
# Override SMALL to cloud (faster)
# Local for BIG/MIDDLE
## Privacy & Security
### Air-Gapped (No Internet)
# Everything local
# Local tracking only
# No external connections
### Proxy Authentication
# .env
# Require auth from clients
### Custom Guardrails
## Reasoning & Extended Thinking
### Maximum Reasoning (GPT-5 / o-series)
# Use reasoning models
# Global reasoning config
### Claude 4 Extended Thinking
# Claude 4 with 16k thinking tokens
# Per-model reasoning overrides
### Gemini 2/3 Extended Thinking
# Gemini 3 with thinking
### Mixed Reasoning Strategy
# High reasoning for complex tasks
# Medium for general tasks
# No reasoning for simple tasks (faster)
# SMALL_MODEL_REASONING not set (disabled)
# Show performance
## Multi-Provider Hybrid
### Local + Cloud Hybrid
# Default: OpenRouter
# BIG: Local Ollama (privacy + free)
# MIDDLE: Gemini (free + fast)
# SMALL: OpenRouter free tier
### Multi-Region Redundancy
# Primary: US region
# BIG: Azure EU (compliance)
# MIDDLE: OpenAI US
# SMALL: Default OpenRouter
### Development vs. Production
# Development
# Production
## Development Workflows
### Code Review Assistant
# Show detailed output
### Documentation Writer
### Debugging Assistant
## Advanced Configurations
### Performance Tuning
# Increase timeouts for large requests
# Retry failed requests
# Token limits
# Show performance metrics
### Custom Headers
# OpenRouter specific
# Custom auth
# User agent
### Rich Terminal Dashboard
# Enable all visual features
### Minimal Terminal Output
# Minimal logs
# Disable dashboard
# Essential info only
## Complete Workflow Examples
### First-Time Setup to First Request
# 1. Clone and install
# 2. Run setup wizard
# Follow prompts...
# 3. Start proxy
# 4. Configure Claude Code
# 5. Use Claude Code
### Switching Between Providers
# Use Gemini
# Switch to OpenRouter
# Switch to local Ollama
### Testing Different Models
# Test model selector
# Search for models, copy names
# Update .env with selected models
# Restart proxy
# Test new models
## Troubleshooting Examples
### Debug 401 Errors
# Enable debug logging
# Check API key
# Test provider directly
# Restart proxy with verbose output
### Verify Configuration
# Check all environment variables
# Test proxy endpoint
# Test with Claude Code
## More Resources


## Content / Data Structure:
```text
# Examples & Use Cases

Practical examples for common Claude Code Proxy setups.

---

## Table of Contents

- [Quick Starts](#quick-starts)
- [Cost Optimization](#cost-optimization)
- [Privacy & Security](#privacy--security)
- [Reasoning & Extended Thinking](#reasoning--extended-thinking)
- [Multi-Provider Hybrid](#multi-provider-hybrid)
- [Development Workflows](#development-workflows)
- [Advanced Configurations](#advanced-configurations)

---

## Quick Starts

### Fastest Setup (Google Gemini - Free)

```bash
# Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# Run setup wizard
python start_proxy.py --setup
# Select: Google Gemini → Enter API key → Done

# Start proxy
python start_proxy.py
```

In another terminal:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "write a fibonacci function"
```

Get Gemini key: https://makersuite.google.com/app/apikey

---

### Local-Only (100% Free, Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull qwen2.5:72b

# Configure proxy
cat > .env << 'EOF'
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:72b"
SMALL_MODEL="qwen2.5:14b"
EOF

# Start proxy
python start_proxy.py
```

In another terminal:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "analyze this code"
```

---

### OpenRouter (352+ Models, Free Tier)

```bash
# Run setup wizard
python start_proxy.py --setup
# Select: OpenRouter → Enter API key → Choose models

# Or manual .env:
cat > .env << 'EOF'
PROVIDER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-flash-1.5"
SMALL_MODEL="x-ai/grok-beta:free"
EOF

# Start proxy
python start_proxy.py
```

Get OpenRouter key: https://openrouter.ai/keys

---

## Cost Optimization

### Free Models Only

Use 100% free models from OpenRouter:

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# All free models
BIG_MODEL="google/gemini-flash-1.5:free"
MIDDLE_MODEL="x-ai/grok-beta:free"
SMALL_MODEL="google/gemini-flash-1.5:free"

# Track usage
TRACK_USAGE="true"
USAGE_DB_PATH="usage.db"
```

**Free models on OpenRouter:**
- `google/gemini-flash-1.5:free`
- `x-ai/grok-beta:free`
- `meta-llama/llama-3.1-8b-instruct:free`
- `mistralai/mistral-7b-instruct:free`
- `nousresearch/hermes-3-llama-3.1-405b:free`

### Tiered Cost Strategy

Expensive models for hard tasks, cheap for easy:

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# Expensive for BIG (complex reasoning)
BIG_MODEL="anthropic/claude-sonnet-4"  # ~$3/M tokens

# Medium for MIDDLE (general tasks)
MIDDLE_MODEL="google/gemini-pro-1.5"   # ~$1.25/M tokens

# Free for SMALL (simple tasks)
SMALL_MODEL="google/gemini-flash-1.5:free"  # $0

# Show cost estimates
TERMINAL_SHOW_COST="true"
TRACK_USAGE="true"
```

**Savings:** ~70% reduction vs. using Claude Sonnet for everything.

### Local for Expensive, Cloud for Fast

```bash
# Default: Local Ollama (free)
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"

# Override SMALL to cloud (faster)
ENABLE_SMALL_ENDPOINT="true"
SMALL_ENDPOINT="https://openrouter.ai/api/v1"
SMALL_API_KEY="sk-or-v1-..."
SMALL_MODEL="google/gemini-flash-1.5:free"

# Local for BIG/MIDDLE
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
```

**Why?** Big tasks use free local model (save money), small tasks use fast cloud (save time).

---

## Privacy & Security

### Air-Gapped (No Internet)

```bash
# Everything local
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"

BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
SMALL_MODEL="llama3.1:8b"

# Local tracking only
TRACK_USAGE="true"
USAGE_DB_PATH="usage.db"

# No external connections
ENABLE_OPENROUTER_SELECTION="false"
```

**Privacy:** No data leaves your machine. Messages never sent to cloud providers.

### Proxy Authentication

Secure your proxy with authentication:

```bash
# .env
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"

# Require auth from clients
PROXY_AUTH_KEY="your-super-secret-key-here-min-32-chars"
```

Client configuration:

```bash
export ANTHROPIC_API_KEY="your-super-secret-key-here-min-32-chars"
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "secure request"
```

### Custom Guardrails

Add custom system prompts with safety guidelines:

```bash
ENABLE_CUSTOM_BIG_PROMPT="true"
BIG_SYSTEM_PROMPT_FILE="/path/to/guardrails.txt"
```

**guardrails.txt:**
```
You are a helpful AI assistant for code development.

STRICT RULES:
1. Never generate code that could harm systems or users
2. Always validate user input in code examples
3. Include error handling in all code samples
4. Flag potential security issues in user code
5. Refuse requests for malicious code

Follow these rules without exception.
```

---

## Reasoning & Extended Thinking

### Maximum Reasoning (GPT-5 / o-series)

```bash
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"

# Use reasoning models
BIG_MODEL="gpt-5:high"           # High reasoning effort
MIDDLE_MODEL="o4-mini:50000"     # 50k thinking tokens
SMALL_MODEL="o1-mini:medium"     # Medium reasoning

# Global reasoning config
REASONING_EFFORT="high"          # ~80% tokens for thinking
VERBOSITY="high"                 # Detailed responses
REASONING_EXCLUDE="false"        # Show thinking process
```

**Use cases:** Complex debugging, architectural decisions, mathematical proofs, deep analysis.

### Claude 4 Extended Thinking

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# Claude 4 with 16k thinking tokens
BIG_MODEL="anthropic/claude-opus-4-20250514:16000"
MIDDLE_MODEL="anthropic/claude-sonnet-4-20250514:8k"
SMALL_MODEL="anthropic/claude-sonnet-4-20250514"

# Per-model reasoning overrides
BIG_MODEL_REASONING="16000"
MIDDLE_MODEL_REASONING="8192"
```

### Gemini 2/3 Extended Thinking

```bash
PROVIDER_API_KEY="your-gemini-key"
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"

# Gemini 3 with thinking
BIG_MODEL="gemini-3-pro-preview-11-2025-thinking:24000"
MIDDLE_MODEL="gemini-2.5-flash-preview:16000"

REASONING_MAX_TOKENS="24000"  # Max thinking tokens
```

**Note:** Gemini supports up to 24,576 thinking tokens.

### Mixed Reasoning Strategy

Different reasoning levels per model tier:

```bash
# High reasoning for complex tasks
BIG_MODEL="gpt-5:high"
BIG_MODEL_REASONING="high"

# Medium for general tasks
MIDDLE_MODEL="o4-mini:30000"
MIDDLE_MODEL_REASONING="medium"

# No reasoning for simple tasks (faster)
SMALL_MODEL="gpt-4o"
# SMALL_MODEL_REASONING not set (disabled)

# Show performance
TERMINAL_SHOW_SPEED="true"
TERMINAL_SHOW_COST="true"
```

---

## Multi-Provider Hybrid

### Local + Cloud Hybrid

```bash
# Default: OpenRouter
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# BIG: Local Ollama (privacy + free)
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="qwen2.5:72b"

# MIDDLE: Gemini (free + fast)
ENABLE_MIDDLE_ENDPOINT="true"
MIDDLE_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/openai/"
MIDDLE_API_KEY="your-gemini-key"
MIDDLE_MODEL="gemini-3-pro-preview-11-2025"

# SMALL: OpenRouter free tier
SMALL_MODEL="x-ai/grok-beta:free"
```

**Benefits:**
- Privacy for sensitive tasks (BIG → local)
- Fast free models for common tasks (MIDDLE → Gemini)
- Fallback free tier (SMALL → OpenRouter)

### Multi-Region Redundancy

```bash
# Primary: US region
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# BIG: Azure EU (compliance)
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="https://eu-resource.openai.azure.com/openai/deployments/gpt-4"
BIG_API_KEY="azure-key"
BIG_MODEL="gpt-4"

# MIDDLE: OpenAI US
ENABLE_MIDDLE_ENDPOINT="true"
MIDDLE_ENDPOINT="https://api.openai.com/v1"
MIDDLE_API_KEY="sk-..."
MIDDLE_MODEL="gpt-4o"

# SMALL: Default OpenRouter
SMALL_MODEL="google/gemini-flash-1.5"
```

### Development vs. Production

Use profiles to switch between dev and prod configs:

**profiles/development.env:**
```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
SMALL_MODEL="llama3.1:8b"
TERMINAL_DISPLAY_MODE="debug"
ENABLE_DASHBOARD="true"
```

**profiles/production.env:**
```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5:free"
TERMINAL_DISPLAY_MODE="normal"
TRACK_USAGE="true"
```

Switch profiles:

```bash
# Development
cp profiles/development.env .env
python start_proxy.py

# Production
cp profiles/production.env .env
python start_proxy.py
```

---

## Development Workflows

### Code Review Assistant

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

BIG_MODEL="anthropic/claude-sonnet-4"
ENABLE_CUSTOM_BIG_PROMPT="true"
BIG_SYSTEM_PROMPT="You are a senior code reviewer. Focus on:
- Security vulnerabilities (XSS, SQL injection, auth issues)
- Performance bottlenecks
- Code maintainability and readability
- Best practices for the language/framework
- Edge cases and error handling

Provide specific, actionable feedback with examples."

# Show detailed output
TERMINAL_DISPLAY_MODE="detailed"
TERMINAL_SHOW_COST="true"
```

### Documentation Writer

```bash
ENABLE_CUSTOM_MIDDLE_PROMPT="true"
MIDDLE_SYSTEM_PROMPT="You are a technical documentation specialist.

When writing docs:
- Use clear, concise language
- Include practical examples
- Add code blocks with syntax highlighting
- Organize with headers and lists
- Anticipate common questions
- Provide troubleshooting tips"

MIDDLE_MODEL="google/gemini-pro-1.5"
```

### Debugging Assistant

```bash
ENABLE_CUSTOM_BIG_PROMPT="true"
BIG_SYSTEM_PROMPT="You are a debugging expert.

When analyzing errors:
1. Identify the root cause (not just symptoms)
2. Explain WHY the error occurs
3. Provide step-by-step fix instructions
4. Suggest preventive measures
5. Include relevant documentation links

Use detailed reasoning to trace the issue."

BIG_MODEL="gpt-5:high"
REASONING_EFFORT="high"
TERMINAL_SHOW_SPEED="true"
```

---

## Advanced Configurations

### Performance Tuning

```bash
# Increase timeouts for large requests
REQUEST_TIMEOUT="180"  # 3 minutes

# Retry failed requests
MAX_RETRIES="3"

# Token limits
MAX_TOKENS_LIMIT="8192"
MIN_TOKENS_LIMIT="100"

# Show performance metrics
SHOW_TOKEN_COUNTS="true"
SHOW_PERFORMANCE="true"
TERMINAL_SHOW_SPEED="true"
```

### Custom Headers

Add custom headers for provider-specific features:

```bash
# OpenRouter specific
CUSTOM_HEADER_HTTP_REFERER="https://your-site.com"
CUSTOM_HEADER_X_TITLE="Claude Code Proxy"

# Custom auth
CUSTOM_HEADER_X_API_KEY="custom-key"
CUSTOM_HEADER_AUTHORIZATION="Bearer custom-token"

# User agent
CUSTOM_HEADER_USER_AGENT="ClaudeCodeProxy/1.0"
```

### Rich Terminal Dashboard

```bash
# Enable all visual features
ENABLE_DASHBOARD="true"
DASHBOARD_LAYOUT="detailed"
DASHBOARD_REFRESH="0.5"
DASHBOARD_WATERFALL_SIZE="30"

TERMINAL_DISPLAY_MODE="detailed"
TERMINAL_COLOR_SCHEME="vibrant"
TERMINAL_SESSION_COLORS="true"
TERMINAL_SHOW_WORKSPACE="true"
TERMINAL_SHOW_CONTEXT_PCT="true"
TERMINAL_SHOW_TASK_TYPE="true"
TERMINAL_SHOW_SPEED="true"
TERMINAL_SHOW_COST="true"
TERMINAL_SHOW_DURATION_COLORS="true"

LOG_STYLE="rich"
SHOW_TOKEN_COUNTS="true"
SHOW_PERFORMANCE="true"
```

### Minimal Terminal Output

```bash
# Minimal logs
TERMINAL_DISPLAY_MODE="minimal"
TERMINAL_COLOR_SCHEME="mono"
LOG_STYLE="plain"
COMPACT_LOGGER="true"

# Disable dashboard
ENABLE_DASHBOARD="false"

# Essential info only
TERMINAL_SHOW_COST="true"
TERMINAL_SHOW_SPEED="false"
TERMINAL_SHOW_WORKSPACE="false"
```

---

## Complete Workflow Examples

### First-Time Setup to First Request

```bash
# 1. Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# 2. Run setup wizard
python setup_wizard.py
# Follow prompts...

# 3. Start proxy
python start_proxy.py &

# 4. Configure Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082

# 5. Use Claude Code
claude "write a function to reverse a string"
```

### Switching Between Providers

```bash
# Use Gemini
cp profiles/gemini.env .env
pkill -f start_proxy.py
python start_proxy.py &
claude "test with Gemini"

# Switch to OpenRouter
cp profiles/openrouter.env .env
pkill -f start_proxy.py
python start_proxy.py &
claude "test with OpenRouter"

# Switch to local Ollama
cp profiles/ollama.env .env
pkill -f start_proxy.py
python start_proxy.py &
claude "test with Ollama"
```

### Testing Different Models

```bash
# Test model selector
python -m src.cli.model_selector
# Search for models, copy names

# Update .env with selected models
nano .env

# Restart proxy
pkill -f start_proxy.py
python start_proxy.py &

# Test new models
claude "hello, which model are you?"
```

---

## Troubleshooting Examples

### Debug 401 Errors

```bash
# Enable debug logging
LOG_LEVEL="DEBUG"
TERMINAL_DISPLAY_MODE="debug"

# Check API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'API Key: {os.getenv(\"PROVIDER_API_KEY\")[:10]}...')"

# Test provider directly
curl -H "Authorization: Bearer $PROVIDER_API_KEY" "$PROVIDER_BASE_URL/models"

# Restart proxy with verbose output
python start_proxy.py
```

### Verify Configuration

```bash
# Check all environment variables
python -c "
from dotenv import load_dotenv
import os
load_dotenv()

print('PROVIDER_API_KEY:', os.getenv('PROVIDER_API_KEY')[:10] + '...' if os.getenv('PROVIDER_API_KEY') else 'NOT SET')
print('PROVIDER_BASE_URL:', os.getenv('PROVIDER_BASE_URL'))
print('BIG_MODEL:', os.getenv('BIG_MODEL'))
print('MIDDLE_MODEL:', os.getenv('MIDDLE_MODEL'))
print('SMALL_MODEL:', os.getenv('SMALL_MODEL'))
"

# Test proxy endpoint
curl http://localhost:8082/v1/models

# Test with Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "test connection"
```

---

## More Resources

- [Configuration Guide](CONFIGURATION.md) - Complete environment variable reference
- [Troubleshooting](TROUBLESHOOTING_401.md) - Fix common issues
- [API Reference](API.md) - HTTP API endpoints

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/cleanup_prompt.md
**File Size:** 2697 bytes

## Features & Sections Declared:
# Task-Focused Repository Cleanup Prompt
# Task-Focused Repository Cleanup Prompt


## Content / Data Structure:
```text
# Task-Focused Repository Cleanup Prompt

Use this prompt to instruct an AI assistant to clean up a cluttered repository based on *purpose* and *utility*, rather than just file types.

---

# Task-Focused Repository Cleanup Prompt

Use this prompt to instruct an AI assistant to transform a cluttered repository into a professional, production-ready project in a single, comprehensive pass.

---

**Prompt:**

> I need you to perform a **"Deep Repository Professionalization"** of this project.
>
> **The Goal:**
> Transform this repository from a collection of scripts into a **Unified, Production-Ready Application**. The end result should be a clean root, a single entry point, and a logical service-oriented architecture.
>
> **The Philosophy:**
> - **Architecture over Organization:** Don't just move files; architect them. Separate *Interface* (CLI/API) from *Implementation* (Services).
> - **Unified Experience:** The user should interact with ONE entry point (e.g., `start_proxy.py` or `main.py`) that exposes all functionality via subcommands.
> - **Safety First:** Preserve secrets, permissions, and build contexts.
>
> **Execution Plan: The Phased Adversarial Protocol**
>
> **Phase 1: Audit & Architect (The Architect & Security Engineer)**
> 1.  **Audit:** Scan `src/utils`, `src/core`, and root. Identify "Junk Drawers".
> 2.  **Architect:** Define the Service Layer. (e.g., `src/services/billing`, `src/services/prompts`).
> 3.  **Security Check:** Identify secrets, permissions, and build contexts that must be preserved.
> 4.  **Stop & Review:** Critique your own plan. "Is this architecture sustainable?"
>
> **Phase 2: The Deep Clean (The Refactorer)**
> 1.  **Explode Junk Drawers:** Move files from `src/utils` to `src/services/<domain>`.
> 2.  **Consolidate:** Merge redundant scripts into the CLI.
> 3.  **Refactor:** Clean up `main.py` and entry points.
>
> **Phase 3: Verification (The QA & DevOps Engineer)**
> 1.  **Fix Imports:** Aggressively update all imports.
> 2.  **Test:** Run `python start_proxy.py --help` and `--validate-config`.
> 3.  **Build Check:** Verify Dockerfiles still build (or at least paths are correct).
>
> **Phase 4: Documentation (The Product Manager)**
> 1.  **Rewrite Docs:** Update `README.md` with the new structure.
> 2.  **Final Adversarial Check:** "If I were a new user, would this make sense?"
>
> **Deliverable:**
> -   A repository that passes the "Adversarial Check".
> -   Zero "Junk Drawers".
> -   A unified, verified CLI.
>
> **Deliverable:**
> -   A fully refactored codebase.
> -   A working, unified CLI.
> -   A verified, import-error-free state.
>
> Please proceed with this plan. Start by auditing the current structure.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/free-cascade.md
**File Size:** 1722 bytes

## Features & Sections Declared:
# Free Model Cascade + Selection History
## TUI Workflow
## Web UI Workflow
## Environment Variables
## Runtime Behavior
## Forcing Cascade In Tests


## Content / Data Structure:
```text
# Free Model Cascade + Selection History

This guide covers the new free-model workflow:
- Dynamic ranked free models (`stealth` vs `evergreen`)
- Model cascade fallback chains
- Model selection history

## TUI Workflow
Run:

```bash
python start_proxy.py --select-models
```

Inside the selector:
- `VIEW HISTORY`: shows recently selected models.
- `MANAGE FREE CASCADE`: builds or edits `BIG_CASCADE`, `MIDDLE_CASCADE`, `SMALL_CASCADE`.
- In model picker:
  - `a`: cycle `RECOMMENDED FREE` -> `RECOMMENDED` -> `ALL MODELS`
  - `h`: open selection history

## Web UI Workflow
In the **Models** tab:
- Enable `Model Cascade (Fallback)`
- Edit cascade chains per tier
- Use:
  - `Apply Free Cascade Template`
  - `Load Ranked Free Models`
  - `Load Selection History`

## Environment Variables
Existing cascade vars are used:

```env
MODEL_CASCADE=true
BIG_CASCADE=model-a,model-b,model-c
MIDDLE_CASCADE=model-d,model-e
SMALL_CASCADE=model-f,model-g
MODEL_CASCADE_DAILY_LIMIT=1000
```

## Runtime Behavior
- Streaming and non-streaming requests use cascade when enabled and tier-matched.
- Usage tracking logs UTC-day model request counts to help monitor limit pressure.
- Daily counters are UTC calendar-day based.
- Cascade events (retry/switch/success/exhausted) are emitted with reason codes.
- The Monitor tab shows cascade switches, success rate, and top fallback reasons.

## Forcing Cascade In Tests
- Set `MODEL_CASCADE_DAILY_LIMIT` to the provider/day threshold you want to enforce.
- Update `daily_model_stats.request_count` for the active UTC day and model in `usage_tracking.db`.
- When `request_count >= MODEL_CASCADE_DAILY_LIMIT`, the proxy preemptively skips that model and moves to the next cascade model.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/research/infrastructure-of-agency.md
**File Size:** 26963 bytes

## Features & Sections Declared:
# The Infrastructure of Agency: A Phylogenetic Analysis of Local Agentic Management Software
#research_paper #infrastructure #agent_orchestration #phylogenetic_analysis
## Abstract
## 1. Introduction
### 1.1 From Framework Analysis to Infrastructure Analysis
### 1.2 Scope and Methodology
## 2. The Ecosystem Catalog
### 2.1 Project Inventory
### 2.2 The Proxy Chain: Architecture of the Core
## 3. Gene Expression Analysis
### 3.1 The Routing Gene
### 3.2 The Orchestration Gene
### 3.3 The State Gene: Two Parallel Strategies
### 3.4 The Compression Gene
### 3.5 The Observability Gene
### 3.6 The Distribution Gene
### 3.7 The Auth Gene
### 3.8 The Modality Gene
## 4. Evolutionary Speciation
### 4.1 The Speciation Tree
### 4.2 Dominant Patterns
### 4.3 Missing Genes
## 5. Relationship to Prior Work
### 5.1 Connection to "Architectures of Agency" (Miller, 2025)
### 5.2 Connection to Academic Literature
### 5.3 The MCP Parallel
## 6. Discussion
### 6.1 The Infrastructure Layer Hypothesis
### 6.2 Convergent Evolution Toward Tiering
### 6.3 The Hook as Event Bus
### 6.4 Limitations
## 7. Conclusion
## Appendix A: Full Gene Expression Matrix
### Design-Only Projects (PRDs, no implementation)
## Appendix B: Data Availability
### Verification Methodology


## Content / Data Structure:
```text
# The Infrastructure of Agency: A Phylogenetic Analysis of Local Agentic Management Software

**By Cheta Z. (Ice-ninja)**  
**April 3, 2026**  
**Supersedes: "Architectures of Agency" (Aaron Miller, July 2025)**

#research_paper #infrastructure #agent_orchestration #phylogenetic_analysis

---

## Abstract

Nine months after the publication of "Architectures of Agency" (Miller, 2025), which classified consumer-facing AI coding frameworks into three archetypes (supervised agents, terminal-native agents, autonomous background agents), a new layer of software has emerged to manage, orchestrate, and optimize those agents in production. This paper maps the **local agentic management ecosystem** — proxy chains, memory tiers, session multiplexers, swarm coordinators, compression layers, and configuration distribution hubs — as expressed across 21 interconnected projects in a single developer's infrastructure. Using a **conceptual gene model**, we trace the evolutionary speciation of eight gene families (Routing, Orchestration, State, Compression, Observability, Distribution, Auth, Modality) across the ecosystem, revealing how the management layer has diverged into distinct strains: Infrastructure, Orchestration, Memory, Observability, Distribution, Modality, and Utility. We find that proxy chaining and tiered architectures have emerged as dominant patterns, that file-based state persists alongside SQLite as a parallel evolutionary strategy, and that hook-based interception has become the primary mechanism for cross-layer communication. This analysis updates and extends the framework taxonomy established in the 2025 paper by examining not the agents themselves, but the infrastructure that enables them to operate sustainably at scale.

---

## 1. Introduction

### 1.1 From Framework Analysis to Infrastructure Analysis

"Architectures of Agency" (Miller, 2025) provided a comprehensive taxonomy of consumer-facing AI coding frameworks, classifying tools like Claude Code, Gemini CLI, Aider, Roo Code, and Cursor along three dimensions: agentic flow, context window engineering, and instruction control. That analysis correctly identified the emergence of the Model Context Protocol (MCP) as a standardization layer and documented the transition from predictive text to goal-driven agency.

What that analysis did not — and could not — predict was the **infrastructure layer that would emerge around these frameworks**. When agents move from experimental use to daily production, several problems emerge that the frameworks themselves do not solve:

1. **Cost**: Claude Code through Claude API costs ~$15-30/day for active use. Without proxy-based model routing, the economics are unsustainable.
2. **Model access**: Different frameworks lock into specific providers. Teams need unified access to OpenRouter, OpenAI, Google, Ollama, and local models through a single interface.
3. **Context limits**: Even 200k-token windows are insufficient for large codebases. Compression and memory tiers are required.
4. **Session management**: Running multiple agents in parallel requires multiplexing, isolation, and coordination.
5. **Configuration drift**: Teams using Claude Code, Qwen, Codex, Gemini, and others need consistent rules, skills, and prompts across all platforms.
6. **Observability**: Understanding what agents are doing, how much they cost, and where they fail requires hook-level interception.

The answer has not been a single monolithic solution, but rather a **speciation event**: a diverse ecosystem of specialized management tools, each expressing different subsets of a shared conceptual genome.

### 1.2 Scope and Methodology

This paper analyzes 17 active projects in a single developer's ecosystem (Table 2), selected because they contain working code and are actively used. An additional 4 projects exist as design-only artifacts (PRDs, specs, test plans) but lack implementation. We use a **conceptual gene model**: identifying irreducible functional units ("genes"), grouping them into families, and measuring their expression strength (1-3) in each project.

This approach is inspired by phylogenetic analysis in evolutionary biology, where gene presence/absence across species reveals evolutionary relationships. Here, we treat each project as an organism and each conceptual gene as a heritable trait.

| Gene Family | Genes | Description |
|---|---|---|
| **Routing** | HTTP Proxy, Model Tiering, Protocol Translation | Request direction and format conversion |
| **Orchestration** | Session Multiplexing, Task Decomposition, Swarm Coordination | Parallel agent management |
| **State** | Memory Tiers, File-Based State, SQLite Persistence | Cross-session persistence |
| **Compression** | Token Compression, Context Optimization | Reducing context window costs |
| **Observability** | Hook Interception, Dashboard, Usage Tracking | Monitoring and analytics |
| **Distribution** | Cross-Platform Sync, Config Normalization | Keeping agents consistent |
| **Auth** | OAuth Flow, API Key Management, Auth Passthrough | Identity and access |
| **Modality** | Voice Interface, TUI, Web UI | Input/output channels |

**Table 1:** The eight conceptual gene families and their constituent genes.

---

## 2. The Ecosystem Catalog

### 2.1 Project Inventory

| # | Project | Tier | Primary Function | Key Pattern |
|---|---|---|---|---|
| 1 | claude-code-proxy | Infrastructure | HTTP proxy + model router | FastAPI, tiered routing, Svelte dashboard |
| 2 | CLIProxyAPI Plus | Infrastructure | Multi-provider OAuth proxy | Docker, OAuth flows, rate limiting |
| 3 | input-compression | Infrastructure | RTK + Headroom compression | Two-layer: shell output + API proxy |
| 4 | Hermes Agent | Agent Framework | Self-improving autonomous agent | Python CLI, skills, cron, SQLite+FTS5 |
| 5 | ClawTeam-OpenClaw | Orchestration | Multi-agent swarm coordination | File-based JSON, tmux, git worktrees |
| 6 | Switchboard (fork) | Orchestration | Session browser + visual workflow | Electron, SQLite, MCP bridge |
| 7 | Switchboard Launcher | Orchestration | TUI multiplexer | Python TUI, subprocess management |
| 8 | aaa-voice-assistant | Modality | Voice interface + memory | Tauri+Python, wake word, Whisper.cpp, JSONL db |
| 9 | multi-agent-workflow | Observability | Real-time monitoring + GitHub | Bun server, WebSocket, SQLite, Vue dashboard |
| 10 | hermes-dashboard | Observability | Hermes monitoring | Bun + TypeScript web app |
| 11 | agents/ | Distribution | Cross-platform config hub | skillshare, sync.sh, 18 platforms |
| 12 | hermes-harness | Testing | Hermes test/config framework | Modular Python, dashboard |
| 13 | git-sync-tui | Utility | Git synchronization TUI | Go, Bubbletea TUI |
| 14 | ebay-tracker | Specialized | eBay listing tracker | Python, SQLite, skills format |
| 15 | model-scraper | Utility | Model info scraping | Python, file state |
| 16 | just-prompt | Utility | Prompt management | YAML, file state |
| 17 | IDE-auto-complete | Utility | IDE autocomplete detection | Node.js/TS, debug classifiers |

**Table 2:** The 21-project ecosystem, classified by tier.

### 2.2 The Proxy Chain: Architecture of the Core

The central nervous system of this ecosystem is a **three-tier proxy chain**:

```
Claude Code / Qwen / Codex / any CLI
         │
         ▼
    ┌─────────┐
    │ Headroom│ :8787  (context compression)
    │         │        RTK: shell output compression
    └────┬────┘
         │
         ▼
    ┌──────────────┐
    │claude-code   │ :8082  (model routing + dashboard)
    │   proxy      │        BIG/MIDDLE/SMALL tier selection
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ CLIProxyAPI  │ :8317  (multi-provider OAuth)
    │    Plus      │        Copilot + Kiro free access
    └──────┬───────┘
           │
           ▼
    External Providers
    (OpenRouter, Gemini, OpenAI, etc.)
```

This chain is the **Routing gene** expressed at maximum strength. Each layer is independently deployable and can be used without the others, but together they form a complete stack: compression → routing → auth → upstream.

The chain topology was not designed top-down; it **emerged through speciation**. CLIProxyAPI existed first (as a standalone OAuth proxy for Copilot). claude-code-proxy was built independently (for model routing). Headroom was a third project (for compression). The `proxies` script then orchestrated them into a chain — the ecosystem assembled itself.

---

## 3. Gene Expression Analysis

### 3.1 The Routing Gene

Routing is the most widely expressed gene, found in 6 of 17 active projects (35%). Its expression takes three forms:

- **HTTP Proxy** (strength 3): claude-code-proxy, CLIProxyAPI Plus, input-compression — full API translation layers
- **Model Tiering** (strength 3): claude-code-proxy, input-compression — BIG/MIDDLE/SMALL routing based on task complexity
- **Protocol Translation** (strength 3): claude-code-proxy, CLIProxyAPI Plus — Anthropic ↔ OpenAI format conversion

**Evolutionary note:** Model tiering has evolved into a sophisticated pattern. claude-code-proxy routes `claude-opus` requests to `gemini-3.1-pro-high`, `claude-sonnet` to `gemini-3-flash`, and `claude-haiku` to `gemini-3.1-flash-lite` — completely abstracting the backend model from the client. This is functionally equivalent to DNS load balancing, but for LLM inference.

### 3.2 The Orchestration Gene

Orchestration is expressed in 6 projects (29%), forming a clear evolutionary lineage:

1. **Switchboard Launcher** (session_mux: 3) — The simplest expression: a TUI that launches multiple AI CLIs in parallel with environment variable injection.
2. **Switchboard (fork)** (session_mux: 3, task_decomposition: 2) — Adds Electron UI, visual workflow engine with 9 step types, 20+ orchestration patterns, broadcast mode.
3. **ClawTeam-OpenClaw** (swarm_coord: 3, task_decomposition: 3, session_mux: 3) — The most complex expression: leader agents spawn worker agents, split tasks via DAG decomposition, coordinate via file-based inboxes, merge results. Uses tmux for isolation and git worktrees for code safety.

The progression is clear: **parallel launch → visual coordination → autonomous swarm**. Each step adds a layer of abstraction between the human and the agents.

### 3.3 The State Gene: Two Parallel Strategies

State management reveals a **bifurcation** in the ecosystem. Two competing strategies persist:

| Strategy | Projects | Mechanism | Strengths |
|---|---|---|---|
| **File-Based State** | ClawTeam (3), agents/ (2), Hermes (2), just-prompt (3) | JSON/YAML files, JSONL | Human-readable, git-trackable, no database dependency |
| **SQLite Persistence** | claude-code-proxy (2), Switchboard (2), Hermes (2), multi-agent-workflow (2), ebay-tracker (2), aaa-voice (1) | SQLite with FTS5 | Queryable, ACID, supports dashboards |

Notably, some projects express **both**: Hermes Agent uses SQLite for session search (FTS5) AND file-based YAML for configuration. This suggests the two strategies are **complementary, not competitive**: files for config, SQLite for queries.

**Memory tiers** represent the ecosystem's most significant unimplemented gene. The `aaa-memory` and `autodidactic-omni-loop` repos contain comprehensive PRDs (from ChatGPT, Gemini, and Opus) for a Hot/Warm/Cold system using ByteRover (JSONL + ripgrep), Graphiti (temporal knowledge graph + Kuzu DB), and MemVid V2 (.mv2 archives). The `aaa-voice-assistant` has a working JSONL memory database with benchmark scripts. But the full three-tier memory system described in the PRDs remains **design-only** — it has not been implemented. This is the ecosystem's largest gap between specification and code.

The Hot/Warm/Cold architecture, if implemented, would be functionally identical to CPU cache hierarchies (L1/L2/L3), suggesting convergent evolution on optimal retrieval latency strategies. The PRDs are thorough — the problem is execution, not design.

### 3.4 The Compression Gene

Compression is expressed in 5 projects but at low-to-moderate strength. The two-layer architecture is notable:

- **Layer 1 (RTK)**: Hooks into CLI output, compresses terminal command results before they reach the agent
- **Layer 2 (Headroom)**: Runs as an API-layer proxy, compresses context windows and optimizes token usage

Together they achieve 95-99% token cost reduction on terminal-heavy workflows. This is the ecosystem's most cost-critical gene.

### 3.5 The Observability Gene

Observability is expressed in 5 projects, forming a **monitoring stack**:

```
Claude Code hooks ──→ HTTP POST ──→ Bun server ──→ SQLite ──→ WebSocket ──→ Dashboard
(Hook Intercept: 3)    (multi-agent-workflow)       (sqlite: 2)    (dashboard: 3, web_ui: 2)

Hermes Agent ──→ hermes-dashboard
(sqlite: 2)       (dashboard: 3, web_ui: 3)

Proxy chain ──→ usage_tracking.db ──→ claude-code-proxy dashboard
(usage_tracking: 3)                      (dashboard: 3)
```

Hook interception (strength 3 in multi-agent-workflow, IDE-auto-complete, input-compression) has become the primary mechanism for cross-layer communication. Claude Code's lifecycle hooks (`UserPromptSubmit`, `Stop`, `PostToolUse`) serve as the ecosystem's **event bus** — any project can listen to any agent's activity by installing hooks.

### 3.6 The Distribution Gene

The `agents/` repository is the ecosystem's **gene library** — a single source of truth containing 94 skills, agents, commands, and hooks that sync to 18+ platforms (Claude Code, Hermes, Qwen, Codex, Gemini CLI, Windsurf, Cursor, Cline, OpenCode, etc.).

Key insight: This is not just config sync. It's **config normalization** — the SKILL.md format is the ecosystem's universal bytecode, understood by 10+ platforms natively. The `sync.sh` orchestration applies platform-specific transformations at sync time.

This mirrors how **MCP** (Model Context Protocol) standardized tool access across frameworks. Where MCP standardizes *tool calling*, the agents/ repo standardizes *agent configuration*.

### 3.7 The Auth Gene

Auth expression is concentrated in 4 projects, with OAuth flow being the most sophisticated (CLIProxyAPI Plus: strength 3). The ecosystem's auth strategy is notable for its **passthrough pattern**: claude-code-proxy validates client API keys but delegates OAuth to upstream providers. This mirrors how reverse proxies handle TLS termination — the proxy handles routing, the upstream handles identity.

### 3.8 The Modality Gene

Modality is the most diverse gene, expressed as three competing output formats:

- **Voice** (aaa-voice-assistant: 3) — STT/TTS with wake word detection, Whisper.cpp GPU acceleration
- **TUI** (Switchboard Launcher: 3, git-sync-tui: 3, claude-code-proxy: 1) — Terminal interfaces for quick access
- **Web UI** (Switchboard: 3, multi-agent-workflow: 2, hermes-dashboard: 3) — Browser-based dashboards

The ecosystem expresses all three simultaneously, suggesting **no single modality dominates** — different tasks require different interfaces.

---

## 4. Evolutionary Speciation

### 4.1 The Speciation Tree

Based on shared gene expression patterns, we can reconstruct an evolutionary tree:

```
                    ┌── claude-code-proxy ───┐
    ROUTING ────────┤── CLIProxyAPI Plus ────┤── Infrastructure
                    └── input-compression ───┘
                    
                    ┌── Switchboard Launcher ──┐
    ORCHESTRATION ──┤── Switchboard (fork) ────┤── Orchestration
                    └── ClawTeam-OpenClaw ─────┘
                    
    STATE ──────────────────────────────────────┤── (unimplemented — PRD-only: aaa-memory, autodidactic-omni-loop, mem2)
    
                    ┌── multi-agent-workflow ──┐
    OBSERVABILITY ──┤── hermes-dashboard ──────┤── Observability
                    └── hermes-harness ────────┘
    
    DISTRIBUTION ───────── agents/ ────────────┤── Distribution
    
    MODALITY ──────────── aaa-voice-assistant ─┤── Modality
    
    SPECIALIZED ───────── ebay-tracker ────────┤── Specialized
    
                    ┌── git-sync-tui ──────────┐
    UTILITY ────────┤── model-scraper ─────────┤── Utility
                    ├── just-prompt ───────────┤
                    └── IDE-auto-complete ─────┘
```

### 4.2 Dominant Patterns

Three patterns have emerged as **convergent evolution** — appearing independently in multiple projects:

1. **Tiered Architecture**: Model tiers (claude-code-proxy: BIG/MIDDLE/SMALL), memory tiers (aaa-memory: Hot/Warm/Cold), compression tiers (input-compression: shell/API). This pattern optimizes for cost-performance tradeoffs by routing complexity to the appropriate resource level.

2. **Hook-Based Event Bus**: Claude Code hooks serve as the ecosystem's primary inter-process communication mechanism. Any project can install hooks to listen to agent activity. This is functionally equivalent to a message queue, but implemented through the agent's own extension points.

3. **File-Based State + SQLite Hybrid**: The most sophisticated projects (Hermes, Switchboard) use both: files for configuration (human-readable, git-trackable) and SQLite for operational data (queryable, ACID-compliant).

### 4.3 Missing Genes

Notable absences in the ecosystem:

- **No automatic parallelism detection**: ClawTeam requires manual task decomposition. The swarm_orchestration research doc (Addendum B) describes the algorithm (topological sort on DAG with antichain extraction) but it has not been implemented.
- **No dynamic model escalation**: "Sonnet fails, upgrade to Opus" is configured statically, not decided at runtime based on task complexity.
- **No mid-session model switching**: Models are selected at request time, not switched mid-conversation based on evolving requirements.
- **No cross-framework agent coordination**: ClawTeam orchestrates multiple instances of the same agent type, not Claude Code + OpenHands + Hermes in one workflow.

These gaps represent the ecosystem's **next speciation events** — the genes that will likely emerge in the next evolutionary cycle.

---

## 5. Relationship to Prior Work

### 5.1 Connection to "Architectures of Agency" (Miller, 2025)

This paper extends Miller's framework taxonomy in two directions:

1. **Vertical extension**: Miller analyzed the agents themselves; this paper analyzes the infrastructure *around* them. Where Miller identified three agent archetypes (supervised, terminal-native, autonomous), we identify seven infrastructure archetypes (proxy, orchestrator, memory, observer, distributor, authenticator, modality).

2. **Horizontal extension**: Miller's analysis covered frameworks as standalone products. This paper shows how those frameworks are **connected into a pipeline** through proxy chaining, hook interception, and configuration distribution.

### 5.2 Connection to Academic Literature

- **QualityFlow** (academic agentic workflow): Emphasizes team-like agent specialization. Our ecosystem achieves this through ClawTeam's swarm coordination rather than QualityFlow's pipeline architecture.
- **Token Arbitrage** (Sep 2025): Cloud provider cost-optimized routing. Our ecosystem achieves equivalent results through local proxy-based model tiering rather than cloud arbitrage.
- **OpenClaw's delegation patterns**: Validated in our ecosystem through ClawTeam-OpenClaw's leader/worker pattern.
- **Capy's two-agent architecture** (Captain/Builder): Mirrored in Switchboard's Planner/Executor pattern and ClawTeam's decomposer/worker pattern.

### 5.3 The MCP Parallel

The Model Context Protocol (MCP) standardized tool access across AI frameworks. The agents/ repository achieves an analogous standardization for **agent configuration** through SKILL.md. Both represent a move from proprietary silos to open interoperability — MCP at the tool layer, SKILL.md at the configuration layer.

---

## 6. Discussion

### 6.1 The Infrastructure Layer Hypothesis

We propose that **every sufficiently mature agent deployment spontaneously generates an infrastructure layer**. This is not a design decision but an emergent property: agents in production create cost, complexity, and observability problems that the agents themselves cannot solve, driving the evolution of specialized management tools.

The ecosystem analyzed in this paper is evidence for this hypothesis: 21 projects, none of which are agents themselves, all of which exist to manage agents.

### 6.2 Convergent Evolution Toward Tiering

The repeated emergence of tiered architectures (model tiers, memory tiers, compression tiers) suggests that **cost-performance optimization is the primary selective pressure** on agentic infrastructure. Every successful project expresses some form of tiering — routing complexity to the cheapest resource that can handle it.

### 6.3 The Hook as Event Bus

Claude Code's lifecycle hooks have become the ecosystem's de facto event bus, enabling cross-project communication without requiring a dedicated message queue. This is an elegant solution that leverages the agent's own extension points, but it has limitations: hooks are synchronous, blocking, and tied to a specific agent's lifecycle. A dedicated event bus (Redis pub/sub, NATS) would enable asynchronous, cross-agent event streaming.

### 6.4 Limitations

This analysis covers a single developer's ecosystem, which introduces selection bias. The patterns identified may not generalize to enterprise deployments or multi-developer teams. However, the ecosystem's diversity (17 active projects, 7 tiers, 8 gene families) and the convergence of patterns across independently-developed projects suggest that the findings are not idiosyncratic.

Notably, three of the most thoroughly specified projects (aaa-memory, autodidactic-omni-loop, mem2) exist only as PRDs — comprehensive design documents from multiple models (ChatGPT, Gemini, Opus) with no corresponding implementation. This reveals a **design-implementation gap** that is itself an interesting finding: the ecosystem's most architecturally ambitious ideas have not survived contact with the reality of coding time.

---

## 7. Conclusion

Nine months after "Architectures of Agency" classified the consumer-facing framework landscape, a rich infrastructure layer has emerged to manage those frameworks in production. This ecosystem of 17 active projects (plus 4 design-only artifacts) expresses eight conceptual gene families across seven tiers, with proxy chaining, tiered routing, and hook-based event buses as dominant patterns.

The next evolutionary cycle will likely see: automatic parallelism detection, dynamic model escalation, mid-session model switching, cross-framework agent coordination, and a dedicated event bus replacing synchronous hooks. These gaps represent the frontier of agentic management software — the genes that have not yet emerged but will be necessary for the ecosystem to scale beyond a single developer.

The most striking finding is the **design-implementation gap**: the ecosystem's most architecturally ambitious ideas (three-tier memory, closed-loop learning, alternative memory designs) exist only as PRDs. Three different models (ChatGPT, Gemini, Opus) have independently produced comprehensive specifications for the same problem, but no code has been written. This suggests that in a single-developer ecosystem, **design capacity exceeds implementation capacity** — a bottleneck that autonomous coding agents may eventually resolve.

The infrastructure of agency is not designed; it **speciates**. Each new tool emerges to solve a specific production problem, and the shared genome of conceptual genes reveals the underlying unity of what appears to be a diverse ecosystem.

---

## Appendix A: Full Gene Expression Matrix

| Project | proxy | model_tiering | protocol_translation | session_mux | task_decomposition | swarm_coord | memory_tiers | file_state | sqlite_persist | token_compress | context_opt | hook_intercept | dashboard | usage_tracking | cross_sync | config_norm | oauth_flow | api_key_mgmt | passthrough | voice | tui | web_ui |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-code-proxy | 3 | 3 | 3 | | | | | | 2 | | | 1 | 3 | 3 | | | | 2 | | | 1 | |
| CLIProxyAPI Plus | 3 | | 2 | | | | | | | | 1 | | | | | | 3 | 2 | | | | |
| input-compression | 2 | 1 | | | | | | | | 3 | 3 | 2 | | | | | | | | | | |
| Hermes Agent | | | | 2 | | | 1 | 2 | 2 | | | 1 | 1 | | 2 | 2 | | | | | 2 | |
| ClawTeam-OpenClaw | | | | 3 | 3 | 3 | | 3 | | | | | | | 1 | | | | | | | |
| Switchboard (fork) | | | | 3 | 2 | | | | 2 | | | 1 | 2 | | | | | | | | | 3 |
| Switchboard Launcher | | 1 | | 3 | | | | | | | | | | | | | | | | | 3 | |
| multi-agent-workflow | | | | | | | | | 2 | | | 3 | 3 | 2 | | | | | | | | 2 |
| hermes-dashboard | | | | | | | | | 1 | | | | 3 | | | | | | | | | 3 |
| agents/ | | | | | | | | 2 | | | | | | | 3 | 3 | | | | | | |
| aaa-voice-assistant | | | | | | | 1 | 1 | 1 | | | | | | | | | | | 3 | 1 | 1 |
| hermes-harness | | | | 1 | | | | 3 | | | | | 1 | | | 1 | | | | | | |
| git-sync-tui | | | | | | | | | | | | | | | 1 | | | | | | 3 | |
| ebay-tracker | | | | | | | | 2 | 2 | | | | 1 | | | | | 1 | | | | |
| model-scraper | 1 | | | | | | | 2 | | | | | | | | | | 1 | | | | |
| just-prompt | | | | | | | | 3 | | | | | | | | 1 | | | | | | |
| IDE-auto-complete | 1 | | | | | | | | | | | 2 | | | | | | | | | 1 | |

_Strength scale: 0 (not expressed), 1 (weakly expressed), 2 (moderately expressed), 3 (strongly expressed)._

### Design-Only Projects (PRDs, no implementation)

| Project | Tier | Description | Status |
|---|---|---|---|
| aaa-memory | Memory | Hot/Warm/Cold PRDs from ChatGPT, Gemini, Opus | PRD-only |
| autodidactic-omni-loop | Memory | design.md, requirements.md | PRD-only |
| mem2 | Memory | Alternative memory design | PRD-only |
| barter_agent | Specialized | Unrelated files (frontend-design-masterclass) | Not relevant |

---

## Appendix B: Data Availability

All 17 active projects are available locally at `/home/cheta/code/`. The alluvial genealogy visualization is available at `docs/research/alluvial-graph.html` (note: visualization data reflects initial 21-project survey; gene expression matrix in Appendix A is the verified, corrected source of truth). The conceptual gene model and expression data are available in the tables above.

### Verification Methodology

Gene expression claims were verified against live repository data by:
1. Inspecting directory structures for architectural pattern claims (e.g., `src/dashboard/` for dashboard gene)
2. Grep-searching for key identifiers (e.g., `big_model` for model tiering, `hook` for interception)
3. Checking `package.json` / `go.mod` / `pyproject.toml` for technology stack claims
4. Distinguishing between projects with working code and design-only artifacts (PRDs, specs, test plans)

This verification process reduced the initial survey from 21 to 17 active projects, with 4 classified as design-only.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/research/synthetic-cortex.md
**File Size:** 37359 bytes

## Features & Sections Declared:
# THE SYNTHETIC CORTEX — Fractal Biomimetic Orchestration
## Comprehensive System Architecture & .claude Component Definitions
## Overview
# Part I: The Paradigm
## 1. The Core Thesis
### The Three Hard Problems Solved
## 2. The Biological Analogy
## 3. Semantic Mixture of Experts (SMoE)
# Part II: The Three-Layer Architecture
## Layer 1: The Prime Orchestrator (Strategy Layer)
## Layer 2: The Council (Tactical Layer)
## Layer 3: The Swarm (Execution Layer)
# Part III: The Dual-Definition Codex
## Component Matrix
# Part IV: The .claude Folder — File-by-File Definitions
## 1. CLAUDE.md (Root — The Prime Orchestrator)
# IDENTITY
# MODEL CONFIGURATION
# DIRECTIVES
# ARCHITECTURAL AWARENESS
# THE COUNCIL PROTOCOL
# STATE MANAGEMENT
# OUTPUT FORMAT
## 2. Council Agent Definitions (Layer 2)
### 2a. council_strategist.md
# IDENTITY
# STRICT RULES
# SCRIPT TEMPLATE
# OUTPUT FORMAT
### 2b. council_analyst.md
# IDENTITY
# RESPONSIBILITIES
# CONSTRAINTS
# OUTPUT
## 3. Swarm Agent Definitions (Layer 3)
### 3a. worker_scout.md
# IDENTITY
# EXECUTION PROTOCOL
# OUTPUT FORMAT
# FORBIDDEN
### 3b. worker_analyst.md
# IDENTITY
# EXECUTION PROTOCOL
# OUTPUT FORMAT
# FORBIDDEN
### 3c. worker_submitter.md
# IDENTITY
# EXECUTION PROTOCOL
# OUTPUT FORMAT
# FORBIDDEN
## 4. Skills (Procedural Memory)
### 4a. council_debate.md
# COUNCIL DEBATE PROTOCOL
## Purpose
## Process
## Mission Spec Template
## Stop Conditions
## Governance
### 4b. swarm_dispatch.md
# SWARM DISPATCH PATTERN
## Core Template
## Parameter Guide
## Error Handling Rules
### 4c. dom_extraction.md
# DOM EXTRACTION HEURISTICS
## Form Detection Priority
## Field Identification
## CAPTCHA Detection
## Confidence Scoring
## Anti-Patterns
## 5. Hooks (Autonomic Regulation)
### 5a. budget_governor.js
#!/usr/bin/env node
### 5b. post_error_logger.sh
#!/bin/bash
# .claude/hooks/post_error_logger.sh
# Triggered: PostToolUse on any tool that returned an error
# Purpose: Log errors to state directory for later analysis
# Extract error info from the tool output (passed via stdin or env)
## 6. State Management (Shared Memory)
### 6a. budget.json
### 6b. current_mission.json
### 6c. retry_queue.json
## 7. MACS Integration (The Spinal Cord)
## 8. Proxy Integration (The Thalamus)
# Part V: The Execution Flow
## The Life of a Mission
# Part VI: Market Position & Competitive Analysis
## Why This Architecture Is Leading
## Why Others Haven't Done This
# Part VII: The Employment Strategy
## The "Proof of Work" Resume
# Part VIII: Footnotes


## Content / Data Structure:
```text
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

```


---


