# Crosstalk System - Model-to-Model Conversations

A powerful system for facilitating conversations between multiple AI models using Exchange-of-Thought (EoT) communication paradigms.

## Features

### 🎯 Four Communication Paradigms

1. **Memory Paradigm**
   - Models analyze independently and share insights
   - Best for: Brainstorming, research, collecting diverse perspectives
   - Each model stores its reasoning in memory

2. **Report Paradigm**
   - Sequential reporting between models
   - Best for: Structured discussions, status updates, progress reports
   - Each model reports to the next in sequence

3. **Relay Paradigm** (Default)
   - Chain communication through all models
   - Best for: Continuous conversation, building on ideas
   - Each model responds to the previous one's message

4. **Debate Paradigm**
   - Contradictory reasoning with confidence evaluation
   - Best for: Exploring different viewpoints, challenging assumptions
   - Models challenge each other's positions

### 🔧 Multiple Interface Options

- **REST API**: Full-featured API for programmatic use
- **CLI**: Interactive wizard and command-line interface
- **MCP Server**: Integration with Claude Desktop and other MCP-compatible clients
- **Configuration Files**: YAML-based configuration for repeatability

## Quick Start

### 1. Interactive Setup (Recommended First Time)

```bash
python start_proxy.py --crosstalk-init
```

This launches an interactive wizard that guides you through:
- Selecting models (BIG, MIDDLE, SMALL)
- Configuring system prompts (from files or inline)
- Choosing communication paradigm
- Setting iterations and topic

### 2. Command-Line Arguments

```bash
python start_proxy.py \
  --crosstalk big,small \
  --system-prompt-big path:examples/prompts/alice.txt \
  --system-prompt-small path:examples/prompts/bob.txt \
  --crosstalk-iterations 20 \
  --crosstalk-topic "hery whats up" \
  --crosstalk-paradigm debate
```

### 3. Configuration File

Create a YAML file:

```yaml
models:
  - big
  - small

system_prompts:
  big: path:examples/prompts/alice.txt
  small: path:examples/prompts/bob.txt

paradigm: debate
iterations: 20

topic: "What are the most important challenges facing AI?"
```

Then run:

```bash
python start_proxy.py --crosstalk-config my-config.yaml
```

## API Usage

### Setup Crosstalk Session

```bash
curl -X POST http://localhost:8082/v1/crosstalk/setup \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["big", "small"],
    "system_prompts": {
      "big": "path:examples/prompts/alice.txt",
      "small": "path:examples/prompts/bob.txt"
    },
    "paradigm": "debate",
    "iterations": 20,
    "topic": "hery whats up"
  }'
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "configured",
  "models": ["big", "small"],
  "paradigm": "debate",
  "iterations": 20
}
```

### Execute Crosstalk

```bash
curl -X POST http://localhost:8082/v1/crosstalk/550e8400-e29b-41d4-a716-446655440000/run \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "duration_seconds": 45.2,
  "conversation": [
    {
      "speaker": "big",
      "listener": "small",
      "content": "...",
      "iteration": 0,
      "timestamp": 1234567890.0,
      "confidence": 0.85,
      "message_type": "opening"
    }
  ]
}
```

### Check Status

```bash
curl http://localhost:8082/v1/crosstalk/550e8400-e29b-41d4-a716-446655440000/status
```

### List All Sessions

```bash
curl http://localhost:8082/v1/crosstalk/list
```

### Delete Session

```bash
curl -X DELETE http://localhost:8082/v1/crosstalk/550e8400-e29b-41d4-a716-446655440000/delete
```

## MCP Server Integration

The MCP server allows you to use crosstalk from Claude Desktop and other MCP-compatible clients.

### Setup

1. Edit Claude Desktop configuration:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

2. Add the crosstalk MCP server:

```json
{
  "mcpServers": {
    "claude-code-proxy-crosstalk": {
      "command": "uv",
      "args": [
        "run",
        "/ABSOLUTE/PATH/TO/claude-code-proxy/src/api/mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here",
        "BIG_MODEL": "gpt-4o",
        "MIDDLE_MODEL": "gpt-4o-mini",
        "SMALL_MODEL": "gpt-4o-mini"
      }
    }
  }
}
```

3. Restart Claude Desktop

### Available MCP Tools

After setup, you can use these tools in Claude:

- **`crosstalk_setup`** - Configure a new crosstalk session
- **`crosstalk_run`** - Execute a configured crosstalk
- **`crosstalk_status`** - Check session status
- **`crosstalk_list`** - List all active sessions
- **`crosstalk_delete`** - Delete a session
- **`load_system_prompt`** - Load custom system prompt for a model
- **`crosstalk_health`** - Check system health

### Example MCP Usage in Claude

```
Use the crosstalk_setup tool to set up a conversation between big and small models with the debate paradigm, 20 iterations, topic "AI ethics"
```

Claude will then ask if you want to run it, and you can use `crosstalk_run` to execute.

## System Prompts

### File-Based Prompts

Create a text file with your system prompt:

```bash
# examples/prompts/alice.txt
You are Alice, an enthusiastic and optimistic AI assistant.
You love exploring new ideas and always look for creative solutions.
```

Reference it with the `path:` prefix:

```bash
--system-prompt-big path:examples/prompts/alice.txt
```

### Inline Prompts

Pass directly on the command line:

```bash
--system-prompt-big "You are Alice, a helpful assistant who loves to explore ideas."
```

### Environment Configuration

Set persistent configuration via environment variables:

```bash
export ENABLE_CUSTOM_BIG_PROMPT="true"
export BIG_SYSTEM_PROMPT_FILE="examples/prompts/alice.txt"

export ENABLE_CUSTOM_SMALL_PROMPT="true"
export SMALL_SYSTEM_PROMPT_FILE="examples/prompts/bob.txt"
```

## Examples

### Example 1: Basic Relay Conversation

```bash
python start_proxy.py \
  --crosstalk big,middle,small \
  --crosstalk-iterations 10 \
  --crosstalk-topic "Explain quantum computing to a child"
```

### Example 2: Debate with Custom Prompts

```bash
python start_proxy.py \
  --crosstalk big,small \
  --system-prompt-big path:examples/prompts/alice.txt \
  --system-prompt-small path:examples/prompts/bob.txt \
  --crosstalk-paradigm debate \
  --crosstalk-iterations 15 \
  --crosstalk-topic "Should AI systems be regulated?"
```

### Example 3: Memory Paradigm for Research

```bash
python start_proxy.py \
  --crosstalk big,middle,small \
  --crosstalk-paradigm memory \
  --crosstalk-iterations 5 \
  --crosstalk-topic "Research the benefits and risks of quantum computing"
```

### Example 4: Report Paradigm for Status Updates

```bash
python start_proxy.py \
  --crosstalk big,small \
  --crosstalk-paradigm report \
  --crosstalk-iterations 8 \
  --crosstalk-topic "Provide a project status update for each team member"
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BIG_MODEL` | Model ID for BIG requests | `claude-3-opus` |
| `MIDDLE_MODEL` | Model ID for MIDDLE requests | `claude-3-sonnet` |
| `SMALL_MODEL` | Model ID for SMALL requests | `claude-3-haiku` |
| `BIG_ENDPOINT` | Custom endpoint for BIG | None |
| `MIDDLE_ENDPOINT` | Custom endpoint for MIDDLE | None |
| `SMALL_ENDPOINT` | Custom endpoint for SMALL | None |
| `ENABLE_CUSTOM_BIG_PROMPT` | Enable custom BIG prompt | `false` |
| `ENABLE_CUSTOM_MIDDLE_PROMPT` | Enable custom MIDDLE prompt | `false` |
| `ENABLE_CUSTOM_SMALL_PROMPT` | Enable custom SMALL prompt | `false` |
| `BIG_SYSTEM_PROMPT_FILE` | File path for BIG prompt | None |
| `MIDDLE_SYSTEM_PROMPT_FILE` | File path for MIDDLE prompt | None |
| `SMALL_SYSTEM_PROMPT_FILE` | File path for SMALL prompt | None |

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--crosstalk-init` | Launch interactive setup wizard |
| `--crosstalk MODELS` | Quick setup with comma-separated models |
| `--system-prompt-big PROMPT` | System prompt for BIG model |
| `--system-prompt-middle PROMPT` | System prompt for MIDDLE model |
| `--system-prompt-small PROMPT` | System prompt for SMALL model |
| `--crosstalk-iterations N` | Number of iterations (1-100) |
| `--crosstalk-topic TEXT` | Initial topic/message |
| `--crosstalk-paradigm PARADIGM` | Paradigm: memory, report, relay, debate |

## Testing

Run the test suite to verify your setup:

```bash
python test_crosstalk.py
```

This tests:
- System prompt loading
- Crosstalk orchestrator
- API endpoints
- CLI integration
- MCP server
- Example files

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface                             │
│  (Interactive Wizard + Command-Line Arguments)              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Crosstalk Orchestrator                          │
│  - Session Management                                        │
│  - Paradigm Execution (Memory/Report/Relay/Debate)          │
│  - Model Communication                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌────────▼────────────┐
│   OpenAI Client  │    │   Custom System     │
│                  │    │   Prompt Loader     │
│  - Model Routing │    │                     │
│  - Request/Response│    │  - File Loading     │
└──────────────────┘    │  - Inline Prompts    │
                        └─────────────────────┘
                                 │
                    ┌────────────▼──────────┐
                    │   Per-Model Clients   │
                    │                       │
                    │  BIG │ MIDDLE │ SMALL │
                    │      │        │       │
                    └───────────────────────┘
```

## Best Practices

1. **Choose the Right Paradigm**
   - Memory: Brainstorming, research, collecting insights
   - Report: Structured discussions, updates
   - Relay: Continuous conversation, building on ideas
   - Debate: Exploring viewpoints, challenging assumptions

2. **Custom System Prompts**
   - Use file-based prompts for consistency
   - Keep prompts concise but descriptive
   - Test prompts with single model before crosstalk

3. **Iteration Limits**
   - Start with 5-10 iterations for testing
   - Increase to 20+ for complex topics
   - Monitor token usage and costs

4. **Topic Selection**
   - Start with clear, specific topics
   - Avoid overly broad topics without structure
   - Consider adding constraints to guide conversation

5. **Model Selection**
   - Mix BIG and SMALL for cost efficiency
   - Use all three for diverse perspectives
   - Consider model strengths (reasoning vs. speed)

## Troubleshooting

### Session Not Found
```
❌ Error: Session 550e8400-e29b-41d4-a716-446655440000 not found
```
**Solution**: Ensure you ran `crosstalk_setup` first and the session hasn't been deleted.

### No API Key
```
❌ Error: API key not configured
```
**Solution**: Set `OPENAI_API_KEY` environment variable or configure in `.env` file.

### MCP Server Not Working
```
❌ MCP library not available
```
**Solution**: Install with `pip install mcp`

### Models Not Responding
```
❌ Error: Failed to call model
```
**Solution**:
- Check API key validity
- Verify model IDs in config
- Check network connectivity
- Review model endpoint URLs

## Contributing

The crosstalk system is designed to be extensible. To add new paradigms:

1. Add enum value to `CrosstalkParadigm` in `src/conversation/crosstalk.py`
2. Implement `_execute_<paradigm>` method
3. Add tests in `test_crosstalk.py`
4. Update documentation

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
1. Run `test_crosstalk.py` to identify problems
2. Check logs in the terminal output
3. Review this documentation
4. Create an issue on GitHub

---

**Built with ❤️ using Exchange-of-Thought (EoT) communication paradigms**
