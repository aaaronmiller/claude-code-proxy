# Examples

Practical examples for using The Ultimate Proxy.

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Analytics & Monitoring](#analytics--monitoring)
3. [CLI Tool Integration](#cli-tool-integration)
4. [Advanced Configuration](#advanced-configuration)

---

## Basic Usage

### Start the Proxy

```bash
# Quick start (interactive setup)
python quickstart.py

# Or manual start
python start_proxy.py

# With debug logging
LOG_TIER=debug python start_proxy.py
```

### Configure Claude Code

```bash
# Set proxy URL
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY=pass

# Run Claude Code
claude
```

### Add Shell Aliases

Add to `~/.zshrc`:

```bash
# Toggle proxy
cproxy() {
  if [[ -n "$ANTHROPIC_BASE_URL" ]]; then
    unset ANTHROPIC_BASE_URL
    echo "🎯 Direct to Anthropic"
  else
    export ANTHROPIC_BASE_URL=http://localhost:8082
    export ANTHROPIC_API_KEY=pass
    echo "🔀 Using proxy"
  fi
}

# Start proxy
alias ccproxy='cd ~/code/claude-code-proxy && python start_proxy.py'
```

---

## Analytics & Monitoring

### Check System Health

```bash
# Basic health
curl http://localhost:8082/api/system/health

# Comprehensive diagnostics
curl http://localhost:8082/api/system/health/diagnostic | jq
```

### View Real-time Metrics

```bash
# Aggregate metrics
curl http://localhost:8082/api/metrics/aggregate | jq '.metrics'

# Active sessions
curl http://localhost:8082/api/metrics/sessions | jq '.sessions[] | {id: .session_id, requests, tokens, cost}'

# Specific session
curl http://localhost:8082/api/metrics/sessions/abc123... | jq
```

### Tool Call Analytics

```bash
# Last 24 hours
curl http://localhost:8082/api/metrics/tool-analytics | jq

# Last 7 days
curl "http://localhost:8082/api/metrics/tool-analytics?hours=168" | jq

# Filter by session
curl "http://localhost:8082/api/metrics/tool-analytics?session_id=abc123" | jq
```

### Cache Performance

```bash
# Cache analytics
curl http://localhost:8082/api/metrics/cache-analytics | jq

# Output:
# {
#   "cache_hit_rate": 67.1,
#   "cached_tokens": 45230,
#   "token_savings_percent": 36.2,
#   "estimated_cost_savings": 0.0452
# }
```

### Historical Trends

```bash
# Get 30 days of trends
curl "http://localhost:8082/api/metrics/history/trends?days=30" | jq '.trends'

# Plot with jq (simple text chart)
curl "http://localhost:8082/api/metrics/history/trends?days=30" | jq -r '
  .trends | 
  "Date\t\tTool Calls\tSuccess Rate\n" +
  ([range(0; .tool_calls | length)] | 
   map("\(.trends.dates[.])\t\(.trends.tool_calls[.])\t\(.trends.tool_success_rate[.])%") | 
   join("\n"))
'
```

---

## CLI Tool Integration

### View All CLI Tools

```bash
curl http://localhost:8082/api/cli-tools | jq '.data.tools | keys'

# Output: ["claude", "opencode", "openclaw", "hermes", "qwen"]
```

### Get CLI Tool Stats

```bash
curl http://localhost:8082/api/cli-tools/stats | jq '.stats'

# Output:
# {
#   "total_tools": 5,
#   "total_sessions": 16,
#   "all_models": ["opus", "sonnet", "coder-model"],
#   "config_file_types": {"CLAUDE.md": 2, "AGENTS.md": 1}
# }
```

### Session Timeline

```bash
# Last 7 days
curl http://localhost:8082/api/cli-tools/timeline | jq '.timeline[] | {tool: .tool_name, session: .session_id, time: .timestamp}'

# Filter by tool
curl "http://localhost:8082/api/cli-tools/timeline?tool=claude&days=3" | jq
```

### Specific Tool Details

```bash
# Claude Code details
curl http://localhost:8082/api/cli-tools/claude | jq '.data'

# Output includes:
# - Settings
# - Sessions
# - Config files (CLAUDE.md, etc.)
# - Models used
# - Plugins enabled
```

---

## Advanced Configuration

### Enable Debug Logging

```bash
# In .env or environment
LOG_TIER=debug
LOGS_DIR=logs
LOG_MAX_SIZE_MB=100
LOG_RETENTION_DAYS=3

# Start proxy
python start_proxy.py
```

### View Log History

```bash
# Run cleanup (aggregates then cleans)
python -m src.services.logging.log_cleanup

# View history
python -m src.services.logging.log_cleanup --view-history

# Show last 30 entries
python -m src.services.logging.log_cleanup --view-history --history-limit 30
```

### Configure Model Cascade

```bash
# In .env
MODEL_CASCADE=true

# Fallback chain for BIG model
BIG_CASCADE=openai/gpt-4o,anthropic/claude-3-opus,google/gemini-pro

# Fallback chain for MIDDLE model  
MIDDLE_CASCADE=openai/gpt-4o-mini,anthropic/claude-3-sonnet

# Fallback chain for SMALL model
SMALL_CASCADE=openai/gpt-4o-mini,google/gemini-flash
```

### Set Up Cron for Log Cleanup

```bash
# Edit crontab
crontab -e

# Add daily cleanup at 3 AM
0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup >> /var/log/claude-cleanup.log 2>&1
```

### Monitor with Watch

```bash
# Watch aggregate metrics
watch -n 5 'curl -s http://localhost:8082/api/metrics/aggregate | jq ".metrics | {sessions: .total_sessions, requests: .total_requests, tokens: .total_tokens}"'

# Watch active sessions
watch -n 10 'curl -s http://localhost:8082/api/metrics/sessions | jq ".count"'
```

---

## Troubleshooting

### Check if Proxy is Running

```bash
curl http://localhost:8082/api/system/health
```

### View Recent Errors

```bash
curl http://localhost:8082/api/system/health/diagnostic | jq '.logs.recent_errors'
```

### Check Provider Status

```bash
curl http://localhost:8082/api/system/health/diagnostic | jq '.providers'
```

### Verify Database

```bash
curl http://localhost:8082/api/system/health/diagnostic | jq '.database'
```

---

## Useful One-Liners

```bash
# Total cost today
curl -s http://localhost:8082/api/metrics/aggregate | jq '.metrics.total_cost'

# Tool success rate
curl -s http://localhost:8082/api/metrics/tool-analytics | jq '.success_rate'

# Cache savings
curl -s http://localhost:8082/api/metrics/cache-analytics | jq '.estimated_cost_savings'

# Active CLI tools count
curl -s http://localhost:8082/api/cli-tools/stats | jq '.stats.total_tools'

# Sessions in last hour
curl -s http://localhost:8082/api/system/health/diagnostic | jq '.requests.last_hour'
```

---

*Examples for version 2.1.0 | Last updated: March 30, 2026*
