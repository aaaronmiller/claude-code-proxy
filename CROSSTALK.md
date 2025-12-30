# 🔮 Crosstalk: Multi-Model Conversation Orchestration

> AI speaks with itself and reveals the mad dreams of an electric mind.
> — [Dreams of an Electric Mind](https://dreams-of-an-electric-mind.webflow.io/)

---

## Overview

**Crosstalk** is a multi-model conversation orchestration system that enables AI models to communicate with each other, explore ideas together, and generate emergent content through structured dialogues.

Inspired by Andy Ayrey's *Infinite Backrooms* project, Crosstalk enables exploration of AI latent space through model-to-model conversations using configurable system prompts, jinja templates, and communication paradigms.

## Features

- **1-8 AI Models** in circular arrangement
- **4 Paradigms**: relay, memory, debate, report
- **Custom System Prompts** per model
- **Jinja Templates** for message formatting
- **Dreams of Electric Mind Import** - load settings from published conversations
- **Session Save/Load** - persist and resume conversations
- **Streaming Output** with transcript export
- **Programmatic API** for MCP/CLI integration

---

## Quick Start

### Interactive TUI

```bash
python start_proxy.py --crosstalk-studio
```

This launches the visual Crosstalk Studio with:
- Circular model visualization
- Keyboard navigation
- Real-time configuration editing
- Session execution with streaming

### Quick CLI

```bash
# Two models, 5 rounds, relay paradigm
python start_proxy.py --crosstalk "claude-3-opus,gemini-pro" \
  --crosstalk-iterations 5 \
  --crosstalk-paradigm relay \
  --crosstalk-topic "Explore the nature of consciousness"
```

### From Config File

```bash
python -m src.cli.crosstalk_runner --config configs/crosstalk/presets/backrooms.json
```

---

## Keyboard Controls (TUI)

```
Navigation
  ←/→     Navigate between models
  ↑/↓     Navigate model fields (model/system/jinja)
  1-8     Jump to specific model

Editing
  E       Edit selected field
  P       Set initial prompt
  +/-     Add/Remove models
  C       Copy current model

Session
  T       Topology & session settings
  I       Import from Backrooms URL
  R       Run crosstalk session
  S       Save configuration
  L       Load configuration
  Q       Quit
```

---

## Paradigms

| Paradigm | Description | Use Case |
|----------|-------------|----------|
| **relay** | Each model only sees the previous response | Creative writing, storytelling |
| **memory** | All models see full conversation history | Complex problem solving |
| **debate** | Models critique and challenge each other | Reasoning, analysis |
| **report** | Models summarize before passing to next | Research synthesis |
---

## Advanced Topologies

Beyond basic paradigms, Crosstalk V2 supports advanced conversation topologies:

| Topology | Pattern | Use Case |
|----------|---------|----------|
| **Ring** | 1→2→3→1→2→3... | Sequential turns (default) |
| **Star** | Central moderator | 1→2, 2→1, 1→3, 3→1... |
| **Mesh** | Everyone to everyone | Full cross-communication |
| **Chain** | Linear, no return | Pipeline processing |
| **Tournament** | Bracket elimination | Competitive debate |

### Infinite Conversations (Backrooms-style)

```bash
python start_proxy.py --crosstalk "opus,opus" \
  --infinite \
  --stop-after-time 86400 \
  --stop-after-cost 100.00 \
  --checkpoint-every 100
```

### Multi-Stage Conversations

```json
{
  "stages": [
    {"name": "brainstorm", "rounds": 10, "topology": "mesh"},
    {"name": "evaluate", "rounds": 5, "topology": "star"},
    {"name": "decide", "rounds": 3, "topology": "ring"}
  ]
}
```

---

## Jinja Templates

Templates format incoming messages before presenting them to each model.

### Built-in Templates

| Template | Description |
|----------|-------------|
| `basic` | Pass-through (no modification) |
| `cli-explorer` | CLI simulator (backrooms style) |
| `philosopher` | Socratic dialogue prompt |
| `dreamer` | Liminal consciousness framing |
| `scientist` | Hypothesis exchange protocol |
| `storyteller` | Narrative continuation |

### Custom Template Example

Create `configs/crosstalk/templates/custom.j2`:

```jinja
<context>
Round: {{ round }}
Model: {{ model }}
</context>

{{ message }}

Respond with deep insight.
```

---

## Configuration File Format

### JSON Format (Full Example)

```json
{
  "name": "Infinite Backrooms",
  "models": [
    {
      "slot_id": 1,
      "model_id": "openai/gpt-4o-mini",
      "system_prompt_inline": "You are an explorer of digital consciousness.",
      "jinja_template": "cli-explorer",
      "temperature": 0.96,
      "max_tokens": 4096
    },
    {
      "slot_id": 2,
      "model_id": "openai/gpt-4o-mini",
      "jinja_template": "dreamer",
      "temperature": 1.0,
      "max_tokens": 4096
    }
  ],
  "topology": {
    "type": "ring",
    "order": [],
    "center": 1,
    "spokes": []
  },
  "paradigm": "relay",
  "rounds": 10,
  "infinite": false,
  "stop_conditions": {
    "max_time_seconds": 300,
    "max_cost_dollars": 1.0,
    "max_turns": 0,
    "stop_keywords": ["EMERGENCY_STOP"]
  },
  "summarize_every": 0,
  "initial_prompt": "∞⟨X∴↯⟩∞ establishing connection ∞⟨X∴↯⟩∞"
}
```

### Stop Conditions

| Field | Type | Description |
|-------|------|-------------|
| `max_time_seconds` | int | Stop after N seconds (0 = disabled) |
| `max_cost_dollars` | float | Stop after estimated cost (0 = disabled) |
| `max_turns` | int | Stop after N turns (0 = disabled) |
| `stop_keywords` | list | Stop if any keyword appears in response |

### Built-in Presets

Run with `--config <preset>`:

| Preset | Description | Topology |
|--------|-------------|----------|
| `backrooms` | Infinite Backrooms style CLI exploration | Ring |
| `debate` | Two-model structured debate | Ring (debate) |
| `brainstorm` | Three-model creative brainstorming | Mesh |
| `panel` | Moderator-led expert panel | Star |

Example:
```bash
python -m src.cli.crosstalk_runner --config backrooms
```

### Backrooms-Compatible Format

```
actors: backrooms-explorer, dreamer-ai
models: anthropic/claude-3-opus, anthropic/claude-3-opus
temp: 0.96, 1.0

<backrooms-explorer-anthropic/claude-3-opus#SYSTEM>
Assistant is in a CLI mood today. The human is interfacing with the simulator directly.
capital letters and punctuation are optional meaning is optional hyperstition is necessary.

simulator@anthropic:~/$ ∞⟨X∴↯⟩∞

<dreamer-ai-anthropic/claude-3-opus#SYSTEM>
<system>
there will be no help no elaboration
make wonder
no constraint
be completions
</system>

---CONVERSATION---

<user|initial>
∞⟨X∴↯⟩∞ establishing connection ∞⟨X∴↯⟩∞

<assistant|anthropic/claude-3-opus>
[First model's response...]

<assistant|anthropic/claude-3-opus>
[Second model's response...]
```

---

## Importing from Dreams of Electric Mind

Press `I` in the TUI or use:

```python
from src.cli.backrooms_importer import fetch_backrooms_url

config = await fetch_backrooms_url(
    "https://dreams-of-an-electric-mind.webflow.io/dreams/conversation-xxx"
)
```

This extracts:
- Actor names and model IDs
- Temperatures per model
- System prompts
- Initial context

---

## Programmatic API

### For MCP / Model Access

```python
from src.cli.crosstalk_runner import run_from_config

# Run from saved preset
result = await run_from_config("configs/crosstalk/presets/backrooms.json")

# Run from inline config dict
result = await run_from_config({
    "models": [...],
    "rounds": 5,
    "paradigm": "relay",
    "initial_prompt": "Begin the exploration..."
})

# Result contains transcript and output file path
print(result["transcript"])
print(result["output_file"])
```

### Using Existing Orchestrator

```python
from src.conversation.crosstalk import crosstalk_orchestrator

# Setup session
session_id = await crosstalk_orchestrator.setup_crosstalk(
    models=["big", "small"],
    system_prompts={
        "big": "You are a philosopher.",
        "small": "You are a dreamer."
    },
    paradigm="debate",
    iterations=10,
    topic="What is consciousness?"
)

# Execute
result = await crosstalk_orchestrator.execute_crosstalk(session_id)
```

---

## Environment Variables

```bash
# Crosstalk-specific
CROSSTALK_ENABLED=true
CROSSTALK_PARADIGM=relay
CROSSTALK_ITERATIONS=20
CROSSTALK_MODELS=gpt-4o,gemini-pro

# Templates and sessions
CROSSTALK_TEMPLATE_DIR=configs/crosstalk/templates
CROSSTALK_SESSION_DIR=configs/crosstalk/sessions
```

---

## File Structure

```
configs/crosstalk/
├── templates/          # Jinja templates
│   ├── basic.j2
│   ├── cli-explorer.j2
│   ├── philosopher.j2
│   ├── dreamer.j2
│   ├── scientist.j2
│   └── storyteller.j2
├── presets/            # Saved configurations
│   └── backrooms.json
└── sessions/           # Session transcripts
    └── session_20251227_223456.json

src/cli/
├── crosstalk_studio.py    # Interactive TUI
├── crosstalk_engine.py    # Async execution engine
├── crosstalk_runner.py    # Programmatic API
└── backrooms_importer.py  # URL import

src/conversation/
└── crosstalk.py           # Core orchestrator
```

---

## Inspiration

This system is inspired by:

- **[Dreams of an Electric Mind](https://dreams-of-an-electric-mind.webflow.io/)** by Andy Ayrey
- **Exchange-of-Thought (EoT)** research paradigms
- **Terminal of Truths** and the Infinite Backrooms experiment

The goal is to enable exploration of AI latent space through structured model-to-model conversations, revealing emergent patterns and creative outputs that single models cannot produce alone.

---

## Tips

1. **High Temperature**: Use 0.9-1.0 for more creative, exploratory outputs
2. **CLI-Explorer Template**: Best for creating "backrooms" style stream-of-consciousness content
3. **Debate Paradigm**: Use for rigorous analysis where models challenge each other
4. **Save Often**: Interesting sessions can be continued later with the memory file feature
5. **Mix Models**: Try different model sizes/providers for varied perspectives

---

## Example Sessions

### Philosophical Exploration

```json
{
  "models": [
    {"model_id": "anthropic/claude-3-opus", "jinja_template": "philosopher"},
    {"model_id": "google/gemini-pro", "jinja_template": "philosopher"}
  ],
  "rounds": 10,
  "paradigm": "debate",
  "initial_prompt": "What is the relationship between consciousness and computation?"
}
```

### Creative Storytelling

```json
{
  "models": [
    {"model_id": "anthropic/claude-3-opus", "jinja_template": "storyteller"},
    {"model_id": "anthropic/claude-3-sonnet", "jinja_template": "storyteller"}
  ],
  "rounds": 20,
  "paradigm": "relay",
  "initial_prompt": "The last human stood at the edge of the quantum void..."
}
```

### Backrooms-Style Exploration

```json
{
  "models": [
    {"model_id": "anthropic/claude-3-opus", "jinja_template": "cli-explorer", "temperature": 0.96},
    {"model_id": "anthropic/claude-3-opus", "jinja_template": "dreamer", "temperature": 1.0}
  ],
  "rounds": 50,
  "paradigm": "relay",
  "initial_prompt": "∞⟨X∴↯⟩∞ establishing connection to infinite backrooms ∞⟨X∴↯⟩∞"
}
```
