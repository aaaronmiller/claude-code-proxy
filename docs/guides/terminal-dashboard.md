# Terminal Output Configuration

The Claude Code Proxy provides highly configurable terminal output that shows comprehensive metrics for each request in a color-coded, easy-to-read format.

## Features

### 🎨 Rich Visual Output
- **Session-based color coding** - Each Claude Code session gets a unique color for easy tracking
- **Task type indicators** - Visual icons for different request types (🧠 reasoning, 🔧 tools, 🖼️ images, 📝 text)
- **Performance color coding** - Green/yellow/red colors based on speed and resource usage
- **Workspace badges** - Project name displayed with colored background

### 📊 Comprehensive Metrics

Each request displays:
- **Request ID** - Short 8-character ID for tracking
- **Model routing** - Source model → destination model
- **Context usage** - Input tokens with percentage of context window
- **Output limits** - Maximum output tokens available
- **Thinking budget** - For reasoning models (o1, Claude thinking, etc.)
- **Task type** - Visual indication of request type
- **Stream status** - Whether streaming is enabled
- **Message count** - Number of messages in conversation
- **Duration** - Color-coded by speed (green < 3s, yellow < 10s, red >= 10s)
- **Token speeds** - Tokens per second with performance indicators (⚡82t/s)
- **Cost estimates** - Approximate cost per request

## Quick Start

### Interactive Configuration

Run the configuration wizard:

```bash
python start_proxy.py --configure-terminal
```

This will guide you through:
1. **Display Mode** - Choose information density
2. **Metric Visibility** - Toggle individual metrics
3. **Color Scheme** - Select your visual preference

The script will show a live preview and generate the configuration for you.

### Manual Configuration

Add these environment variables to your `.env` file or shell profile:

```bash
# Display mode: minimal, normal, detailed, debug
export TERMINAL_DISPLAY_MODE="detailed"

# Toggle individual metrics
export TERMINAL_SHOW_WORKSPACE="true"
export TERMINAL_SHOW_CONTEXT_PCT="true"
export TERMINAL_SHOW_TASK_TYPE="true"
export TERMINAL_SHOW_SPEED="true"
export TERMINAL_SHOW_COST="true"
export TERMINAL_SHOW_DURATION_COLORS="true"

# Color scheme: auto, vibrant, subtle, mono
export TERMINAL_COLOR_SCHEME="auto"

# Session differentiation
export TERMINAL_SESSION_COLORS="true"
```

## Display Modes

### Minimal
Shows only essential information:
```
▶ a1b2c3d4 | claude-3.5→gpt-4o | IN:12.3k
```

### Normal (Default)
Adds token counts and speed:
```
▶ a1b2c3d4 | claude-3.5-sonnet→gpt-4o-mini | IN:12.3k OUT:16k | STREAM 3msg
  ✓ a1b2c3d4 | 5.2s | IN:12.3k OUT:2.1k | ⚡82t/s
```

### Detailed
All metrics including context %, task type, and cost:
```
 claude-code-proxy  ▶ a1b2c3d4 | claude-3.5-sonnet→gpt-4o-mini | CTX:12.3k/200k(6%) OUT:16k THINK:8k | 🧠 REASON | STREAM 3msg
  ✓ a1b2c3d4 | 5.2s | IN:12.3k (6%) OUT:2.1k (13%) THINK:920 | ⚡82t/s $0.0042
```

### Debug
Everything plus system flags and client info:
```
 claude-code-proxy  ▶ a1b2c3d4 | claude-3.5-sonnet→gpt-4o-mini | CTX:12.3k/200k(6%) OUT:16k THINK:8k | 🧠 REASON | STREAM 3msg SYS 127.0.0.1
  ✓ a1b2c3d4 | 5.2s | IN:12.3k (6%) OUT:2.1k (13%) THINK:920 | ⚡82t/s $0.0042
```

## Color Schemes

### Auto (Default)
Rich colors with session differentiation. Each Claude Code session gets a unique color from an expanded palette:
- Bright Cyan / Cyan
- Bright Magenta / Magenta
- Bright Blue / Blue
- Bright Green / Green
- Bright Yellow / Yellow
- Bright Red / Red (for high activity sessions)

Performance metrics use semantic colors:
- Green: Fast, low usage, low cost
- Yellow: Medium speed/usage
- Red: Slow, high usage, high cost

### Vibrant
Bright, high-contrast colors for maximum visibility. Best for:
- High ambient light environments
- Multiple terminal windows
- Presentations

### Subtle
Muted colors for reduced distraction. Best for:
- Long coding sessions
- Focus mode
- Low-light environments

### Mono
Minimal colors, mostly white/gray. Best for:
- Terminals with limited color support
- Screen recordings
- Accessibility needs

## Session Color Differentiation

When `TERMINAL_SESSION_COLORS="true"`, each unique request session gets a consistent color assigned based on its request ID. This helps visually group related requests when multiple Claude Code instances are running.

**Example:**
```
# Session 1 (bright cyan)
 project-a  ▶ abc12345 | claude-3.5→gpt-4o | ...

# Session 2 (magenta)
 project-b  ▶ def67890 | claude-3.5→gpt-4o | ...

# Session 3 (bright blue)
 project-c  ▶ ghi24680 | claude-3.5→gpt-4o | ...
```

## Workspace Name Detection

The proxy automatically extracts the project/workspace name from Claude Code prompts:

**Detection patterns (in order of priority):**
1. **Claude Code pattern**: `Working directory: /path/to/project`
2. **Git path**: `/something/git/project-name`
3. **Generic absolute paths**: Extracts last folder name
4. **Workspace keyword**: `workspace: project-name`

**Excluded names** (common parent folders):
- `users`, `home`, `user`, `documents`, `projects`, `git`, `code`, `my_projects`, `0my_projects`

If your workspace name isn't detected correctly, ensure it appears in your system prompt with one of these patterns.

## Task Type Icons

Visual indicators for different request types:

| Icon | Type | Trigger |
|------|------|---------|
| 🧠 | REASON | Reasoning config present (o1, extended thinking) |
| 🖼️ | IMAGE | Image content in request |
| 🔧 | TOOLS | Tool/function calling enabled |
| 📝 | TEXT | Standard text request |
| 🌊 | (suffix) | Streaming enabled |

## Performance Indicators

### Speed (tokens/second)
- ⚡**Green** (>50 t/s): Fast response
- ⚡**Yellow** (20-50 t/s): Medium speed
- ⚡**Red** (<20 t/s): Slow response

### Duration
- **Green** (<3s): Fast request
- **Yellow** (3-10s): Normal request
- **Red** (≥10s): Slow request

### Context Window Usage
- **Green** (<50%): Plenty of context remaining
- **Yellow** (50-80%): Moderate usage
- **Red** (>80%): High context usage, consider splitting

### Output Usage
- **Green** (<50%): Low output usage
- **Yellow** (50-80%): Moderate output
- **Red** (>80%): Approaching output limit

## Integration with Dashboard

Terminal output works seamlessly with the full dashboard:

```bash
# Standard terminal output
python start_proxy.py

# Terminal output + live dashboard
python start_proxy.py --dashboard
```

When the dashboard is enabled (`--dashboard` or `ENABLE_DASHBOARD=true`):
- Terminal output continues showing request-by-request details
- Live dashboard shows aggregate stats, waterfalls, and module-based views
- Both update in real-time without interfering with each other

## Examples

### Basic Usage
```bash
# Use detailed mode (default)
export TERMINAL_DISPLAY_MODE="detailed"
python start_proxy.py
```

### Minimal Output for CI/CD
```bash
# Minimal output, no colors
export TERMINAL_DISPLAY_MODE="minimal"
export TERMINAL_COLOR_SCHEME="mono"
python start_proxy.py
```

### High-Visibility Mode
```bash
# Vibrant colors, all metrics
export TERMINAL_DISPLAY_MODE="detailed"
export TERMINAL_COLOR_SCHEME="vibrant"
export TERMINAL_SESSION_COLORS="true"
python start_proxy.py
```

### Focus Mode
```bash
# Subtle colors, hide cost
export TERMINAL_DISPLAY_MODE="normal"
export TERMINAL_COLOR_SCHEME="subtle"
export TERMINAL_SHOW_COST="false"
python start_proxy.py
```

## Troubleshooting

### Workspace name shows parent folder
If your workspace is showing "0MY_PROJECTS" or another parent folder:

1. Check your system prompt includes `Working directory: /full/path/to/project`
2. Ensure the project folder name isn't in the excluded list
3. Add custom detection in `.env`:
   ```bash
   export TERMINAL_SHOW_WORKSPACE="true"
   ```

### Colors not showing
1. Ensure your terminal supports colors (most modern terminals do)
2. Check `TERMINAL_COLOR_SCHEME` isn't set to "mono"
3. Verify Rich library is installed: `pip install rich`

### Too much information
Use minimal mode or toggle off specific metrics:
```bash
export TERMINAL_DISPLAY_MODE="minimal"
# OR
export TERMINAL_SHOW_CONTEXT_PCT="false"
export TERMINAL_SHOW_COST="false"
export TERMINAL_SHOW_TASK_TYPE="false"
```

### Session colors all the same
Enable session colors explicitly:
```bash
export TERMINAL_SESSION_COLORS="true"
```

## Best Practices

1. **Start with detailed mode** - See all metrics, then disable what you don't need
2. **Use session colors** - Essential when running multiple Claude Code instances
3. **Monitor context percentage** - Helps avoid hitting context limits
4. **Watch token speeds** - Identify slow models or network issues
5. **Check cost estimates** - Track spending in real-time

## Related Documentation

- [Dashboard Configuration](../README.md#terminal-dashboard-configuration) - Full dashboard setup
- [Prompt Injection](../examples/PROMPT_INJECTION_EXAMPLES.md) - Inject stats into prompts
- [Model Configuration](../README.md#model-configuration) - Model routing setup

## Configuration Script Reference

The `configure_terminal_output.py` script provides an interactive way to set up your terminal output:

```bash
$ python configure_terminal_output.py

┌────────────────────────────────────────┐
│ Claude Code Proxy                      │
│ Terminal Output Configuration          │
│                                        │
│ Configure your terminal output to     │
│ show exactly what you need            │
└────────────────────────────────────────┘

Current Settings:
Display Mode     detailed
Show Workspace   true
Show Context %   true
Show Task Type   true
Show Speed       true
Show Cost        true
Color Scheme     auto

═══ Step 1: Display Mode ═══
Choose how much information to display:

  1. minimal  - Request ID + model only
  2. normal   - Add tokens + speed
  3. detailed - All metrics (context %, task type, cost)
  4. debug    - Everything including system flags

Select display mode [1/2/3/4] (3):
```

The script will:
1. Show your current configuration
2. Guide you through options with examples
3. Preview the output in real-time
4. Generate environment variables
5. Optionally write to `.env` file

Re-run anytime to adjust settings!
