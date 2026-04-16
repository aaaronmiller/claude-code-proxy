# Status Bar Integration Guide

This proxy provides three tiers of status display:

1. **tmux pane border + bottom status** — when running `proxies up`
2. **Claude Code status line** — integrated via script
3. **Standalone `proxies stats` / `proxies metrics`** — on-demand CLI

## 1. Tmux Status Bars (Automatic)

When you run `proxies up`, a tmux session is launched with these status bars:

### Bottom status bar (all panes)
```
[PROXY: 45req | 182.3K tok | $0.0023 | 340ms | ↺2]  ...  [● HEADROOM | 67% compressed | saved:12.4K] │ [● RTK | 78% saved | 45.2K tok saved]
```

- **Left**: Claude Code Proxy summary (requests, tokens, cost, latency, cascade events)
- **Right**: Headroom compression + RTK terminal compression
- Refresh interval: **5 seconds**

### Pane border (top of each pane)
Shows pane title (service name).

### Script: `scripts/tmux_status.sh`
Callable directly:
```bash
./scripts/tmux_status.sh proxy      # Proxy summary line
./scripts/tmux_status.sh headroom   # Headroom summary line
./scripts/tmux_status.sh rtk        # RTK summary line
```

Returns tmux-formatted strings (with `#[fg=...]` color codes).

## 2. Claude Code Status Line

Add proxy metrics to your Claude Code status bar.

### Standalone (easiest)
Add a single segment to your status line script:

```bash
# In ~/.claude/status-line.sh, add before `build_status_line`:
PROXY_METRICS=$(/home/cheta/code/claude-code-proxy/scripts/cc_statusline_metrics.sh all)
echo -e "$PROXY_METRICS"
```

This outputs a single line like:
```
● Proxy │ ● HR │ ⇒ routed │ 󰊢 182.3K │ 󰠗 45✓/2✗ │ 󱐋 HR:67% (12.4K) │ 󰚩 RTK:78% (45.2K)
```

### Integrated (recommended)
Source the helper and add its functions to the `metrics` array:

```bash
# In ~/.claude/status-line.sh, near the top:
source /home/cheta/code/claude-code-proxy/scripts/cc_statusline_metrics.sh

# In build_status_line() metrics block, add:
local ph; ph=$(get_proxy_health);       [ -n "$ph" ] && metrics+=("$ph")
local hr; hr=$(get_headroom_savings);   [ -n "$hr" ] && metrics+=("$hr")
local rtk; rtk=$(get_rtk_savings);      [ -n "$rtk" ] && metrics+=("$rtk")
local tools; tools=$(get_tool_stats);   [ -n "$tools" ] && metrics+=("$tools")
local mode; mode=$(get_routing_mode);   [ -n "$mode" ] && metrics+=("$mode")
```

### Available metric functions
| Function | Output example |
|----------|---------------|
| `get_proxy_health` | `● Proxy` (green) or `○ Proxy` (red) |
| `get_headroom_health` | `● HR` or `○ HR` |
| `get_tokens_per_sec` | `󱐋 240tok/s` |
| `get_session_tokens` | `󰊢 182.3K` |
| `get_tool_stats` | `󰠗 45✓/2✗` |
| `get_headroom_savings` | `󱐋 HR:67% (12.4K)` |
| `get_rtk_savings` | `󰚩 RTK:78% (45.2K)` |
| `get_last_proxy_error` | `⚠ gpt-oss-120b:free` |
| `get_routing_mode` | `⇒ routed` / `⇒ passthru` / `⇒ tier` |
| `get_fixed_width_model <name>` | `Nemotron  ` (10-char padded, prevents jitter) |

## 3. Fixing Variable-Width Layout Jitter

The user's existing status line uses cursor-column positioning (`\033[%dG`) for right anchors
which is stable regardless of left content length. However, **line 2 metrics** use
even-gap spacing which changes when any metric's visible width changes.

### Root cause
`gap_each = total_gap / (num_metrics + 1)` — gaps shift when any metric changes width.

### Two-line solution
Use **fixed cursor positions** for each metric slot:

```bash
# Instead of calculating gaps, place each metric at a fixed column.
# E.g., 7 metrics in 180 cols → slot every ~25 cols.

local slot_width=25
for i in "${!metrics[@]}"; do
    local col=$(( 2 + i * slot_width ))
    printf '\033[%dG' "$col"
    printf "%b" "${metrics[$i]}"
done
echo
```

This guarantees each metric starts at the same column every time, regardless of
content width — so the bar doesn't jitter when model names or token counts change.

### Single-width solution
Alternatively, use `get_fixed_width_model` to normalize variable-width items:
```bash
local model_display
model_display=$(get_fixed_width_model "$current_model")
# Always 10 chars wide — no jitter
```

## Caching

`cc_statusline_metrics.sh` caches API responses for 5 seconds per endpoint in
`/tmp/.cc_proxy_statusline_$$` (PID-scoped, auto-cleaned on shell exit).
This prevents hammering the proxy API when the status line refreshes every second.

## Configuration

Override endpoints via env vars:
```bash
export PROXY_URL="http://127.0.0.1:8082"      # Claude Code Proxy
export HEADROOM_URL="http://127.0.0.1:8787"   # Headroom compression proxy
```
