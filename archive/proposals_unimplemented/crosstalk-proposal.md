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
