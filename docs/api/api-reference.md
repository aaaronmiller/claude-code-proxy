# API Reference

The Ultimate Proxy provides a REST API for monitoring, analytics, and configuration.

**Base URL:** `http://localhost:8082`

---

## Table of Contents

1. [System Health](#system-health)
2. [Metrics & Analytics](#metrics--analytics)
3. [Session Metrics](#session-metrics)
4. [CLI Tools](#cli-tools)
5. [Historical Data](#historical-data)

---

## System Health

### GET `/api/system/health`

Get basic system health status.

**Response:**
```json
{
  "status": "healthy",
  "uptime": "2h 15m",
  "resources": {
    "cpu_percent": 12.5,
    "memory_mb": 256.3,
    "memory_percent": 1.2
  },
  "database": {
    "enabled": true,
    "size_mb": 12.5,
    "path": "usage_tracking.db"
  }
}
```

### GET `/api/system/health/diagnostic`

Get comprehensive diagnostic information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T19:30:00Z",
  "check_duration_ms": 45.2,
  "uptime": {
    "seconds": 8100,
    "formatted": "2h 15m"
  },
  "resources": {...},
  "logs": {
    "tier": "production",
    "dir": "logs",
    "files": [...],
    "total_size_mb": 0.5,
    "recent_errors": []
  },
  "providers": {
    "default": {"status": "healthy", ...},
    "big": {...},
    "middle": {...},
    "small": {...}
  },
  "database": {...},
  "requests": {
    "last_hour": 156,
    "last_24h": 3420,
    "errors_last_hour": 2,
    "avg_duration_ms": 234.5
  },
  "configuration": {...}
}
```

---

## Metrics & Analytics

### GET `/api/metrics/aggregate`

Get aggregate metrics across all sessions.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-03-30T19:30:00Z",
  "metrics": {
    "total_sessions": 12,
    "total_requests": 156,
    "total_tokens": 245000,
    "total_cost": 0.0234,
    "total_tool_calls": 45,
    "tool_success_rate": 95.5,
    "cache_hit_rate": 67.3,
    "cached_tokens": 82000,
    "avg_tokens_per_request": 1570.5,
    "avg_latency_ms": 234.5,
    "avg_tokens_per_second": 45.2,
    "active_sessions": [...]
  }
}
```

### GET `/api/metrics/sessions`

Get all active session metrics.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-03-30T19:30:00Z",
  "sessions": [
    {
      "session_id": "abc123...",
      "started_at": "2026-03-30T17:00:00Z",
      "requests": 15,
      "input_tokens": 12000,
      "output_tokens": 8000,
      "thinking_tokens": 2000,
      "cached_tokens": 5000,
      "total_tokens": 27000,
      "total_latency_ms": 3500,
      "estimated_cost": 0.0023,
      "tool_calls_total": 5,
      "tool_calls_success": 5,
      "tool_calls_failure": 0,
      "cache_hits": 3,
      "cache_misses": 2,
      "models_used": {"gpt-4o": 10, "gpt-4o-mini": 5},
      "last_activity": "2026-03-30T19:25:00Z"
    }
  ],
  "count": 12
}
```

### GET `/api/metrics/sessions/{session_id}`

Get metrics for a specific session.

**Parameters:**
- `session_id` (path) - Session identifier

**Response:** Same structure as session object in `/api/metrics/sessions`

### GET `/api/metrics/tool-analytics`

Get tool call analytics.

**Parameters:**
- `hours` (query, optional) - Hours to include (default: 24)
- `session_id` (query, optional) - Filter by session

**Response:**
```json
{
  "status": "success",
  "period_hours": 24,
  "total_tool_calls": 156,
  "success_rate": 94.2,
  "tools": {
    "Bash": {
      "total": 85,
      "success": 82,
      "failure": 3,
      "success_rate": 96.5,
      "unique_sessions": 8
    },
    "Read": {
      "total": 42,
      "success": 40,
      "failure": 2,
      "success_rate": 95.2,
      "unique_sessions": 6
    }
  }
}
```

### GET `/api/metrics/cache-analytics`

Get cache usage analytics.

**Parameters:**
- `hours` (query, optional) - Hours to include (default: 24)

**Response:**
```json
{
  "status": "success",
  "period_hours": 24,
  "total_requests": 234,
  "cache_hits": 157,
  "cache_misses": 77,
  "cache_hit_rate": 67.1,
  "cached_tokens": 45230,
  "total_tokens": 125000,
  "token_savings_percent": 36.2,
  "estimated_cost_savings": 0.0452
}
```

---

## Session Metrics

### GET `/api/metrics/history`

Get historical metrics snapshots.

**Parameters:**
- `limit` (query, optional) - Max entries (default: 30)
- `start_date` (query, optional) - Filter start (YYYY-MM-DD)
- `end_date` (query, optional) - Filter end (YYYY-MM-DD)

**Response:**
```json
{
  "status": "success",
  "count": 30,
  "entries": [
    {
      "timestamp": "2026-03-30T03:00:00Z",
      "period_start": "2026-03-29T03:00:00Z",
      "period_end": "2026-03-30T03:00:00Z",
      "tool_calls": {
        "total": 156,
        "success": 147,
        "failure": 9,
        "success_rate": 94.2,
        "by_tool": {...}
      },
      "cache_usage": {
        "hits": 157,
        "misses": 77,
        "hit_rate": 67.1,
        "cached_tokens": 45230
      },
      "sessions": 12,
      "summary": "Period: ... | Tools: 156 calls (94.2% success) | ..."
    }
  ]
}
```

### GET `/api/metrics/history/trends`

Get trend data for charting.

**Parameters:**
- `days` (query, optional) - Days to include (default: 30)

**Response:**
```json
{
  "status": "success",
  "period_days": 30,
  "entry_count": 30,
  "trends": {
    "dates": ["2026-03-01", "2026-03-02", ...],
    "tool_calls": [156, 203, ...],
    "tool_success_rate": [94.2, 96.1, ...],
    "cache_hit_rate": [67.3, 72.1, ...],
    "cached_tokens": [45230, 52100, ...],
    "sessions": [12, 15, ...]
  }
}
```

---

## CLI Tools

### GET `/api/cli-tools`

Get data from all AI coding CLI tools.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-03-30T19:30:00Z",
  "data": {
    "timestamp": "...",
    "tools": {
      "claude": {
        "name": "Claude Code",
        "available": true,
        "settings": {...},
        "sessions": {"count": 16, "items": [...]},
        "config_files": [...],
        "models_used": ["opus"],
        "plugins": [...]
      }
    },
    "summary": {
      "total_tools": 5,
      "total_sessions": 16,
      "total_config_files": 4
    }
  }
}
```

### GET `/api/cli-tools/stats`

Get aggregate CLI tool statistics.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-03-30T19:30:00Z",
  "stats": {
    "total_tools": 5,
    "total_sessions": 16,
    "total_config_files": 4,
    "tools_breakdown": {...},
    "all_models": ["opus", "sonnet", "coder-model"],
    "all_plugins": [...],
    "config_file_types": {"CLAUDE.md": 2, "AGENTS.md": 1}
  }
}
```

### GET `/api/cli-tools/timeline`

Get session timeline from CLI tools.

**Parameters:**
- `days` (query, optional) - Days to include (default: 7)
- `tool` (query, optional) - Filter by tool ID

**Response:**
```json
{
  "status": "success",
  "period_days": 7,
  "session_count": 25,
  "timeline": [
    {
      "tool": "claude",
      "tool_name": "Claude Code",
      "session_id": "abc123...",
      "timestamp": "2026-03-30T18:00:00Z",
      "data": {...}
    }
  ]
}
```

### GET `/api/cli-tools/{tool_id}`

Get detailed data for a specific CLI tool.

**Parameters:**
- `tool_id` (path) - Tool identifier (claude, opencode, etc.)

**Response:** Same structure as tool object in `/api/cli-tools`

---

## Error Responses

### 404 Not Found
```json
{
  "status": "not_found",
  "message": "Session abc123 not found or inactive"
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "error": "Error message details"
}
```

### 503 Service Unavailable
```json
{
  "status": "no_data",
  "message": "No metrics history available yet"
}
```

---

## Rate Limiting

Currently, no rate limiting is enforced on the API endpoints. All endpoints are local-only (bound to 0.0.0.0:8082).

---

## Authentication

No authentication is required for API access. The proxy is designed for local use only. For production deployments, consider adding authentication via:
- API key header
- OAuth2
- Reverse proxy authentication

---

*API version: 2.1.0 | Last updated: March 30, 2026*
