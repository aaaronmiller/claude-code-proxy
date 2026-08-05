# Multi-Provider Proxy Architecture

> **Date:** 2025-12-26  
> **Version:** 1.0.0  
> **Status:** Implementation Plan

---

## Executive Summary

This document details the research findings and implementation plan for enabling the Claude Code proxy to work seamlessly with **any LLM provider** (Gemini/VibeProxy, OpenRouter, OpenAI, Anthropic, Azure, etc.) while allowing independent configuration of Big, Medium, and Small models to use different endpoints.

---

## 1. Research Findings

### 1.1 Provider-Specific Quirks

| Provider | Base URL | API Compatibility | Tool Call Schema | Unique Quirks |
|----------|----------|-------------------|------------------|---------------|
| **Gemini/VibeProxy** | `127.0.0.1:8317` | OpenAI-compatible | Transformed | OAuth token auth, "ghost streams", duplicate history |
| **OpenRouter** | `openrouter.ai/api/v1` | OpenAI-compatible | Normalized | `tools` required in every request, minor parameter differences |
| **OpenAI** | `api.openai.com/v1` | Native | Native | Strict mode for schema conformance, `response_format` |
| **Anthropic** | `api.anthropic.com/v1` | Different | `input_schema` | `tool_use` blocks, `stop_reason: tool_use`, server tools |
| **Azure OpenAI** | Custom | OpenAI-compatible | Native | API version header, different auth |

### 1.2 Tool Call Schema Differences

#### OpenAI/OpenRouter (OpenAI-compatible)
```json
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "tool_name",
      "description": "...",
      "parameters": { "JSON Schema" }
    }
  }],
  "tool_choice": "auto"
}
```

**Response:**
```json
{
  "choices": [{
    "message": {
      "tool_calls": [{
        "id": "call_xxx",
        "type": "function",
        "function": {
          "name": "tool_name",
          "arguments": "{\"param\": \"value\"}"
        }
      }]
    }
  }]
}
```

#### Anthropic (Direct)
```json
{
  "tools": [{
    "name": "tool_name",
    "description": "...",
    "input_schema": { "JSON Schema" }
  }],
  "tool_choice": {"type": "auto"}
}
```

**Response:**
```json
{
  "content": [
    {"type": "text", "text": "..."},
    {
      "type": "tool_use",
      "id": "toolu_xxx",
      "name": "tool_name",
      "input": {"param": "value"}
    }
  ],
  "stop_reason": "tool_use"
}
```

#### Gemini (via VibeProxy)
- Uses OpenAI-compatible format BUT parameter names may differ
- Known transformations required (documented in Tool_Call_Implementation_Report.md)

### 1.3 Parameter Name Divergence by Provider

| Claude CLI Expects | Gemini May Output | OpenRouter May Output | OpenAI Outputs |
|-------------------|-------------------|----------------------|----------------|
| `command` | `prompt`, `code` | `command` | `command` |
| `file_path` | `path`, `filename` | `file_path`, `path` | `file_path` |
| `old_text` | `original`, `before` | `old_text` | `old_text` |
| `pattern` | `query`, `search`, `regex` | `pattern` | `pattern` |

**Key Finding:** OpenAI and OpenRouter generally follow Claude's expected schema more closely. Gemini requires the most transformation.

---

## 2. Unique API Calls Beyond Chat Completions

### 2.1 Claude Code CLI API Surface

| Endpoint | Purpose | Provider Handling Required |
|----------|---------|---------------------------|
| `POST /v1/messages` | Main chat completion | Yes - core proxy function |
| `POST /v1/messages/count_tokens` | Token estimation | Partial - uses local estimation |
| `GET /health` | Health check | No - proxy internal |
| `GET /test-connection` | Connectivity test | Yes - uses provider endpoint |
| `POST /v1/crosstalk/*` | Model-to-model | Yes - multi-model orchestration |

### 2.2 Provider-Specific Endpoints

| Provider | Unique Endpoints | Notes |
|----------|-----------------|-------|
| **Anthropic** | `/v1/messages/batches`, `/v1/files`, `/v1/skills`, `/v1/models` | Beta features, versioned via header |
| **OpenAI** | `/v1/chat/completions`, `/v1/embeddings`, `/v1/models` | Standard OpenAI API |
| **OpenRouter** | `/api/v1/chat/completions`, `/api/v1/models` | Unified multi-model access |
| **Gemini** | N/A (via VibeProxy) | OAuth token rotation required |

### 2.3 Required Provider-Specific Handling

| Concern | Description | Solution |
|---------|-------------|----------|
| **Token Counting** | Anthropic has native endpoint; others don't | Use local estimation (already implemented) |
| **Model Listing** | Each provider has different model catalogs | Provider-aware model mapper |
| **Rate Limits** | Different per provider/tier | Provider-specific headers in responses |
| **Streaming** | Gemini has "ghost streams"; others don't | Deduplication already implemented |
| **Authentication** | Gemini=OAuth, OpenRouter/OpenAI=API key | Provider-specific auth handler |

---

## 3. Current Architecture Analysis

### 3.1 Existing Multi-Endpoint Support

The proxy already supports per-model endpoints via environment variables:

```bash
# Per-model endpoints (already supported)
ENABLE_BIG_ENDPOINT=true
BIG_ENDPOINT=http://localhost:8317/v1    # VibeProxy
BIG_API_KEY=oauth_token

ENABLE_MIDDLE_ENDPOINT=true  
MIDDLE_ENDPOINT=https://openrouter.ai/api/v1
MIDDLE_API_KEY=sk-or-xxx

ENABLE_SMALL_ENDPOINT=true
SMALL_ENDPOINT=https://api.openai.com/v1
SMALL_API_KEY=sk-xxx
```

### 3.2 Gaps in Current Implementation

| Gap | Current Behavior | Required Behavior |
|-----|------------------|-------------------|
| **Provider Detection** | Hardcoded VibeProxy check | Dynamic provider detection from URL |
| **Tool Normalization** | Applied to all responses | Provider-specific normalization |
| **Auth Handling** | VibeProxy-specific OAuth | Provider-adaptive auth |
| **Response Format** | Assumes OpenAI format | Provider-specific response parsing |

---

## 4. Proposed Solution: Provider Adapters

### 4.1 Architecture

```
                    Claude Code CLI
                  (Anthropic API format)
                            |
                            v
                   Claude Code Proxy
    +-----------------------------------------------+
    |              ProviderDetector                 |
    |   Detects provider from endpoint URL/config   |
    +-----------------------------------------------+
                            |
           +----------------+----------------+
           v                v                v
  +-------------+  +-------------+  +-------------+
  |GeminiAdapter|  |OpenRouterAdp|  |OpenAIAdapter|
  | - OAuth auth|  | - API key   |  | - API key   |
  | - Full norm |  | - Light norm|  | - No norm   |
  | - Dedup     |  | - Standard  |  | - Standard  |
  +-------------+  +-------------+  +-------------+
           |                |                |
           +----------------+----------------+
                            v
    +-----------------------------------------------+
    |           Tool Call Normalizer                |
    |   Provider-aware normalization intensity      |
    +-----------------------------------------------+
                            |
            +---------------+---------------+
            v               v               v
       VibeProxy      OpenRouter        OpenAI
```

### 4.2 Provider Detection Logic

```python
def detect_provider(base_url: str) -> str:
    url_lower = base_url.lower()
    
    # VibeProxy/Gemini (Antigravity)
    if "127.0.0.1:8317" in url_lower or "localhost:8317" in url_lower:
        return "gemini"
    
    # OpenRouter
    if "openrouter.ai" in url_lower:
        return "openrouter"
    
    # Anthropic
    if "anthropic.com" in url_lower:
        return "anthropic"
    
    # Azure OpenAI
    if "azure" in url_lower or ".openai.azure.com" in url_lower:
        return "azure"
    
    # OpenAI (default for api.openai.com or unknown)
    if "openai.com" in url_lower:
        return "openai"
    
    # Default to openai-compatible for unknown endpoints
    return "openai_compatible"
```

### 4.3 Normalization Intensity Levels

| Provider | Normalization Level | Description |
|----------|---------------------|-------------|
| `gemini` | **FULL** | All 18+ tool transformations |
| `openrouter` | **LIGHT** | Common mismatches only (Bash, Read) |
| `openai` | **NONE** | Pass through unchanged |
| `anthropic` | **SCHEMA_CONVERT** | Convert Anthropic format to Claude CLI format |
| `azure` | **NONE** | Same as OpenAI |
| `openai_compatible` | **LIGHT** | Defensive normalization |

---

## 5. Implementation Plan

### 5.1 Phase 1: Provider Detection

**File: src/services/providers/provider_detector.py (NEW)**

Create provider detection module with:
- `detect_provider(base_url: str) -> str`
- `get_normalization_level(provider: str) -> str`
- `get_auth_type(provider: str) -> str`

**File: src/core/config.py (MODIFY)**

Add provider detection for each endpoint:
- `big_provider`, `middle_provider`, `small_provider`, `default_provider`

### 5.2 Phase 2: Provider-Aware Normalization

**File: src/services/conversion/response_converter.py (MODIFY)**

Update `normalize_tool_arguments()` to accept provider parameter and apply appropriate normalization level.

### 5.3 Phase 3: Streaming Path Updates

**File: src/services/conversion/response_converter.py (MODIFY)**

Update streaming functions to accept and use provider parameter.

---

## 6. Configuration Schema

```bash
# Big Model (e.g., Gemini 2.5 Pro via VibeProxy)
BIG_MODEL=gemini-2.5-pro
ENABLE_BIG_ENDPOINT=true
BIG_ENDPOINT=http://127.0.0.1:8317/v1
BIG_API_KEY=oauth_auto

# Medium Model (e.g., Claude Sonnet via OpenRouter)
MIDDLE_MODEL=anthropic/claude-sonnet-4
ENABLE_MIDDLE_ENDPOINT=true
MIDDLE_ENDPOINT=https://openrouter.ai/api/v1
MIDDLE_API_KEY=sk-or-v1-xxx

# Small Model (e.g., GPT-4o-mini via OpenAI)
SMALL_MODEL=gpt-4o-mini
ENABLE_SMALL_ENDPOINT=true
SMALL_ENDPOINT=https://api.openai.com/v1
SMALL_API_KEY=sk-xxx
```

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Provider detection false positive | LOW | MEDIUM | Explicit provider override config |
| Breaking existing Gemini flow | LOW | HIGH | Default to current behavior |
| OpenRouter subtle differences | MEDIUM | LOW | Light normalization fallback |
| Performance overhead | LOW | LOW | Skip normalization for openai/azure |

---

## 8. Recommendations

### P0 (Implement Now)
- Provider detection from URL
- Provider-aware normalization
- Streaming path updates

### P1 (Follow-up)
- Explicit provider override in config
- Provider-specific auth handlers
- Anthropic direct API adapter

### P2 (Future)
- Provider-specific rate limit handling
- Model listing per provider
- Cost estimation per provider
