# API Reference

HTTP API endpoints and schemas for Claude Code Proxy.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Chat Completion](#post-v1chatcompletions)
  - [List Models](#get-v1models)
  - [Health Check](#get-health)
  - [Configuration](#configuration-endpoints)
- [Request/Response Formats](#requestresponse-formats)
- [Error Handling](#error-handling)
- [WebSocket Support](#websocket-support)

---

## Overview

Claude Code Proxy implements the Claude API (Anthropic format) and proxies to OpenAI-compatible providers. It exposes the following base endpoints:

**Base URL:** `http://localhost:8082` (default, configurable via `PORT` and `HOST`)

**API Version:** `v1`

**Supported Formats:**
- Request: Claude API format (Anthropic)
- Response: Claude API format (Anthropic)
- Backend: OpenAI API format (converted transparently)

---

## Authentication

### Client Authentication (Optional)

If `PROXY_AUTH_KEY` is set, clients must authenticate:

**Header:**
```
x-api-key: your-proxy-auth-key
```

Or:
```
Authorization: Bearer your-proxy-auth-key
```

**Example:**
```bash
curl http://localhost:8082/v1/models \
  -H "x-api-key: your-proxy-auth-key"
```

**Claude Code Configuration:**
```bash
export ANTHROPIC_API_KEY="your-proxy-auth-key"
export ANTHROPIC_BASE_URL=http://localhost:8082
```

### Provider Authentication

Configured via environment variables:
- `PROVIDER_API_KEY` - API key for backend provider
- `PROVIDER_BASE_URL` - Backend provider's base URL

---

## Endpoints

### POST /v1/messages

Create a chat completion (Claude API format).

**Request Body:**
```json
{
  "model": "claude-opus-4",
  "messages": [
    {
      "role": "user",
      "content": "Write a fibonacci function"
    }
  ],
  "max_tokens": 4096,
  "temperature": 0.7,
  "stream": false
}
```

**Optional Parameters:**
- `system` (string) - System prompt
- `temperature` (number, 0-1) - Sampling temperature
- `top_p` (number, 0-1) - Nucleus sampling
- `top_k` (integer) - Top-k sampling
- `stop_sequences` (array of strings) - Stop generation at these sequences
- `stream` (boolean) - Stream response (SSE)
- `metadata` (object) - Request metadata

**Extended Thinking Parameters:**
```json
{
  "thinking": {
    "type": "enabled",
    "budget_tokens": 16000
  }
}
```

Or for OpenAI format:
```json
{
  "reasoning_effort": "high"
}
```

**Response (Non-streaming):**
```json
{
  "id": "msg_01ABC123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Here's a fibonacci function:\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```"
    }
  ],
  "model": "claude-opus-4",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 87
  }
}
```

**Response (Streaming):**

Server-Sent Events (SSE) with the following event types:

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_01ABC","type":"message","role":"assistant","content":[],"model":"claude-opus-4","stop_reason":null,"usage":{"input_tokens":15,"output_tokens":0}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Here"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"'s a"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":87}}

event: message_stop
data: {"type":"message_stop"}
```

**cURL Example:**
```bash
curl http://localhost:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-proxy-auth-key" \
  -d '{
    "model": "claude-opus-4",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "max_tokens": 1024
  }'
```

**Streaming Example:**
```bash
curl http://localhost:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-proxy-auth-key" \
  -d '{
    "model": "claude-opus-4",
    "messages": [
      {
        "role": "user",
        "content": "Count to 10"
      }
    ],
    "max_tokens": 1024,
    "stream": true
  }'
```

---

### GET /v1/models

List available models.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "claude-opus-4",
      "object": "model",
      "created": 1677649963,
      "owned_by": "anthropic"
    },
    {
      "id": "claude-sonnet-4",
      "object": "model",
      "created": 1677649963,
      "owned_by": "anthropic"
    },
    {
      "id": "claude-haiku-4",
      "object": "model",
      "created": 1677649963,
      "owned_by": "anthropic"
    }
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8082/v1/models \
  -H "x-api-key: your-proxy-auth-key"
```

---

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "provider": {
    "base_url": "https://openrouter.ai/api/v1",
    "model_mapping": {
      "claude-opus-4": "anthropic/claude-sonnet-4",
      "claude-sonnet-4": "google/gemini-pro-1.5",
      "claude-haiku-4": "google/gemini-flash-1.5"
    }
  },
  "features": {
    "streaming": true,
    "reasoning": true,
    "hybrid_mode": false,
    "usage_tracking": true,
    "dashboard": false
  }
}
```

**cURL Example:**
```bash
curl http://localhost:8082/health
```

---

### GET /stats

Get usage statistics (if `TRACK_USAGE=true`).

**Response:**
```json
{
  "total_requests": 1523,
  "total_tokens": {
    "input": 458392,
    "output": 234561,
    "thinking": 89234
  },
  "total_cost": {
    "usd": 12.34
  },
  "models": {
    "claude-opus-4": {
      "requests": 892,
      "tokens": 345234,
      "cost": 8.92
    },
    "claude-sonnet-4": {
      "requests": 531,
      "tokens": 198453,
      "cost": 2.67
    },
    "claude-haiku-4": {
      "requests": 100,
      "tokens": 148266,
      "cost": 0.75
    }
  },
  "time_period": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-31T23:59:59Z"
  }
}
```

**Query Parameters:**
- `start_date` (ISO 8601) - Filter from date
- `end_date` (ISO 8601) - Filter to date
- `model` (string) - Filter by model

**cURL Example:**
```bash
curl "http://localhost:8082/stats?start_date=2025-01-01&model=claude-opus-4" \
  -H "x-api-key: your-proxy-auth-key"
```

---

## Configuration Endpoints

### GET /config

Get current configuration (sensitive values redacted).

**Response:**
```json
{
  "provider": {
    "base_url": "https://openrouter.ai/api/v1",
    "api_key_set": true
  },
  "models": {
    "big": "anthropic/claude-sonnet-4",
    "middle": "google/gemini-pro-1.5",
    "small": "google/gemini-flash-1.5"
  },
  "reasoning": {
    "effort": "high",
    "max_tokens": 16000
  },
  "features": {
    "dashboard": false,
    "usage_tracking": true,
    "hybrid_mode": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8082,
    "log_level": "INFO"
  }
}
```

**cURL Example:**
```bash
curl http://localhost:8082/config \
  -H "x-api-key: your-proxy-auth-key"
```

---

### POST /config/reload

Reload configuration from .env file without restarting.

**Response:**
```json
{
  "status": "success",
  "message": "Configuration reloaded",
  "changes": {
    "big_model": {
      "old": "anthropic/claude-sonnet-4",
      "new": "openai/gpt-4o"
    }
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8082/config/reload \
  -H "x-api-key: your-proxy-auth-key"
```

---

## Request/Response Formats

### Model Name Mapping

The proxy maps Claude model names to your configured models:

| Client Requests | Proxy Routes To | Environment Variable |
|----------------|-----------------|---------------------|
| `claude-opus-4` | Value of `BIG_MODEL` | `BIG_MODEL` |
| `claude-sonnet-4` | Value of `MIDDLE_MODEL` | `MIDDLE_MODEL` |
| `claude-haiku-4` | Value of `SMALL_MODEL` | `SMALL_MODEL` |
| Any other model | Passed through as-is | N/A |

**Example:**

Client request:
```json
{
  "model": "claude-opus-4",
  ...
}
```

Proxy routes to backend with:
```json
{
  "model": "anthropic/claude-sonnet-4",  // Value of BIG_MODEL
  ...
}
```

### Message Format

**Claude API Format (Client → Proxy):**
```json
{
  "role": "user",
  "content": "Hello"
}
```

Or with multiple content blocks:
```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "What's in this image?"
    },
    {
      "type": "image",
      "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": "iVBORw0KG..."
      }
    }
  ]
}
```

**OpenAI Format (Proxy → Backend):**

Converted to:
```json
{
  "role": "user",
  "content": "Hello"
}
```

Or for multimodal:
```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "What's in this image?"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/png;base64,iVBORw0KG..."
      }
    }
  ]
}
```

### Reasoning Tokens

**Claude Format:**
```json
{
  "thinking": {
    "type": "enabled",
    "budget_tokens": 16000
  }
}
```

**OpenAI Format:**
```json
{
  "reasoning_effort": "high"
}
```

**Response includes thinking:**
```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me analyze this step by step..."
    },
    {
      "type": "text",
      "text": "Based on my analysis..."
    }
  ],
  "usage": {
    "input_tokens": 50,
    "output_tokens": 200,
    "cache_read_tokens": 0,
    "cache_creation_tokens": 0
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "model is required",
    "param": "model",
    "code": "missing_required_parameter"
  }
}
```

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (missing or invalid auth) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (unknown endpoint) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |
| 502 | Bad Gateway (backend provider error) |
| 503 | Service Unavailable (proxy down) |
| 504 | Gateway Timeout (backend timeout) |

### Error Types

| Error Type | Description |
|------------|-------------|
| `invalid_request_error` | Request is malformed or missing required fields |
| `authentication_error` | Invalid or missing authentication |
| `permission_error` | Valid auth but insufficient permissions |
| `not_found_error` | Requested resource doesn't exist |
| `rate_limit_error` | Too many requests |
| `api_error` | Backend provider returned an error |
| `overloaded_error` | Proxy or backend is overloaded |

### Common Errors

**401 Unauthorized:**
```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid API key",
    "code": "invalid_api_key"
  }
}
```

**429 Rate Limited:**
```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limit exceeded. Please try again in 60 seconds.",
    "code": "rate_limit_exceeded"
  }
}
```

**502 Bad Gateway:**
```json
{
  "error": {
    "type": "api_error",
    "message": "Backend provider returned an error: Model not found",
    "code": "backend_error",
    "provider_error": {
      "status": 404,
      "message": "Model 'invalid-model' not found"
    }
  }
}
```

---

## WebSocket Support

**Status:** Not currently implemented

WebSocket support for real-time streaming may be added in future versions.

Current streaming uses Server-Sent Events (SSE) via the `stream: true` parameter.

---

## Python SDK Example

```python
import anthropic

# Configure to use proxy
client = anthropic.Anthropic(
    api_key="your-proxy-auth-key",  # PROXY_AUTH_KEY
    base_url="http://localhost:8082"
)

# Create message
message = client.messages.create(
    model="claude-opus-4",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(message.content[0].text)
```

**Streaming:**
```python
with client.messages.stream(
    model="claude-opus-4",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Count to 10"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

## JavaScript/TypeScript SDK Example

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: "your-proxy-auth-key",
  baseURL: "http://localhost:8082",
});

const message = await client.messages.create({
  model: "claude-opus-4",
  max_tokens: 1024,
  messages: [
    { role: "user", content: "Hello!" }
  ],
});

console.log(message.content[0].text);
```

**Streaming:**
```typescript
const stream = await client.messages.stream({
  model: "claude-opus-4",
  max_tokens: 1024,
  messages: [
    { role: "user", content: "Count to 10" }
  ],
});

for await (const event of stream) {
  if (event.type === "content_block_delta") {
    process.stdout.write(event.delta.text);
  }
}
```

---

## Rate Limiting

**Current Status:** Rate limiting is handled by the backend provider.

The proxy does not implement its own rate limiting. Rate limits depend on your backend provider:

- **OpenRouter:** Per-user limits based on tier
- **OpenAI:** 3,500 RPM / 90,000 TPM (free tier)
- **Gemini:** 60 RPM (free tier)
- **Ollama/LM Studio:** No limits (local)

---

## Monitoring & Debugging

### Enable Debug Logging

```bash
LOG_LEVEL="DEBUG"
TERMINAL_DISPLAY_MODE="debug"
```

### View Request/Response

Debug logs show:
- Full request to backend
- Full response from backend
- Token counts
- Latency
- Cost estimates

### Usage Tracking

Enable tracking to monitor:
```bash
TRACK_USAGE="true"
USAGE_DB_PATH="usage.db"
```

Query stats:
```bash
curl http://localhost:8082/stats
```

---

## More Resources

- [Configuration Guide](CONFIGURATION.md) - Environment variables
- [Examples](EXAMPLES.md) - Common setups
- [Troubleshooting](TROUBLESHOOTING_401.md) - Fix issues
