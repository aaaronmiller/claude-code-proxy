# Crosstalk V2 Quick Reference

**TL;DR**: Massive enhancement to crosstalk system with topologies, per-model config, infinite conversations, and more.

## 📐 Topologies

| Type | Use Case | Example Pattern |
|------|----------|----------------|
| **Ring** | Sequential turns | 1→2→3→1→2→3... |
| **Star** | Central moderator | 1→2, 2→1, 1→3, 3→1... |
| **Mesh** | Everyone talks to everyone | 1→2, 1→3, 2→1, 2→3... |
| **Chain** | Linear, no return | 1→2→3→1→2→3 |
| **Random** | Random each turn | Random(1,2,3) |
| **Tournament** | Bracket elimination | 2v3 winner→1 |
| **Custom** | Define exact pattern | Your pattern |
| **Conditional** | Dynamic routing | Based on content |

## 🎛️ Per-Model Configuration

```bash
--model 1=big \
--sysprompt 1=alice.txt \
--append 1="Consider ethics." \
--temp 1=0.7 \
--max-tokens 1=2000 \
--reasoning 1=extended --budget 1=8000
```

## 📁 Config File (Clean!)

```bash
python crosstalk.py --config star_debate.json
```

```json
{
  "topology": {"type": "star", "center": 1, "spokes": [2, 3]},
  "models": [
    {"id": 1, "name": "big", "sysprompt": {"file": "alice.txt"}},
    {"id": 2, "name": "middle", "append": "Focus on tech."},
    {"id": 3, "name": "small", "append": "Consider UX."}
  ],
  "conversation": {
    "init_prompt": "Should AI be regulated?",
    "rounds": 10,
    "final_round": {"prompt": "Give your final verdict."}
  },
  "output": {"file": "debate.json"}
}
```

## 🚀 Advanced Features

### Infinite Conversations (Backrooms-style)
```bash
--infinite \
--stop-after-time 86400 \
--stop-after-cost 100.00 \
--checkpoint-every 100
```

### Voting & Consensus
```json
{
  "final_round": {
    "type": "vote",
    "question": "Should we proceed?",
    "options": ["yes", "no"],
    "tally_method": "majority"
  }
}
```

### Meta-Prompts (Summaries)
```bash
--summarize-every 5 \
--summarizer 1 \
--summary-prompt "Summarize key points."
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

## 🔄 Session Management

```bash
# Use existing Claude Code session
--session 1=abc123

# Create new sessions dynamically
--create-sessions 2 \
--workspace 2=/path/to/project2

# Mix both
--session 1=abc123 --create-sessions 2
```

## 🔌 MCP Integration

From Claude Desktop:

```python
# MCP Tool
{
  "config_file": "star_debate.json",
  "wait_for_completion": true,
  "stream_updates": true
}
```

## 📋 Quick Examples

### Simple Debate
```bash
python crosstalk.py \
  --topology ring \
  --model 1=big --model 2=small \
  --init-prompt "Will AI cause unemployment?" \
  --rounds 10
```

### Star with Moderator
```bash
python crosstalk.py \
  --topology star --center 1 --spokes 2,3 \
  --model 1=big --model 2=middle --model 3=small \
  --sysprompt 1=moderator.txt \
  --init-prompt "Should AI be regulated?" \
  --rounds 15
```

### Mesh Brainstorming
```bash
python crosstalk.py \
  --topology mesh \
  --model 1=big --model 2=middle --model 3=small \
  --init-prompt "How to reduce carbon emissions?" \
  --rounds 5
```

### Infinite Backrooms
```bash
python crosstalk.py \
  --topology ring \
  --model 1=big --model 2=big \
  --infinite \
  --stop-after-time 86400 \
  --stop-after-cost 100
```

## 🎯 Key Improvements

| Before | After |
|--------|-------|
| 4 paradigms | 8+ topologies |
| 2-5 models | 2-10 models |
| Basic config | Full per-model config |
| No session mgmt | Dynamic session creation |
| YAML only | JSON/YAML + rich CLI |
| Fixed rounds | Infinite + stop conditions |
| No advanced features | Voting, meta-prompts, stages |

## 📚 Full Documentation

See **CROSSTALK_V2_PROPOSAL.md** for complete details (1,200+ lines).

**This transforms crosstalk from a simple conversation system into a powerful multi-agent orchestration platform!**
