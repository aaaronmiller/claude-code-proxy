#!/usr/bin/env python3
"""
Direct Proxy Test - Verifies proxy without Claude Code overhead.

Tests multiple providers/models:
- vibeproxy/gemini-3-pro (via VibeProxy antigravity)
- vibeproxy/gemini-opus (via VibeProxy - may be rate limited)
- openrouter/oss-120 (free tier)
- gemini/gemini-3-flash (direct Gemini API)
"""

import os
import sys
import json
import time
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

PROXY_URL = "http://127.0.0.1:8082"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
DB_PATH = PROJECT_ROOT / "usage_tracking.db"

# Provider configurations
# Format: provider_name -> {big: main model, small: tool calling model, base_url, api_key}
PROVIDER_CONFIGS = {
    # Gemini-based Claude models via VibeProxy/Antigravity
    "vibeproxy-gemini-claude-sonnet-thinking": {
        "big": "gemini-claude-sonnet-4-5-thinking",   # Sonnet thinking via Gemini
        "small": "gemini-3-flash",                    # Flash for tool calls
        "timeout": 15,
        "base_url": PROXY_URL,
        "api_key": "pass",  # Proxy sets real key
    },
    "vibeproxy-gemini-claude-opus-thinking": {
        "big": "gemini-claude-opus-4-5-thinking",    # Opus thinking via Gemini
        "small": "gemini-3-flash",                   # Flash for tool calls
        "timeout": 20,
        "base_url": PROXY_URL,
        "api_key": "pass",
    },
    "vibeproxy-gemini-claude-sonnet": {
        "big": "gemini-claude-sonnet-4-5",           # Sonnet (non-thinking) via Gemini
        "small": "gemini-3-flash",                   # Flash for tool calls
        "timeout": 15,
        "base_url": PROXY_URL,
        "api_key": "pass",
    },
    # Direct Gemini models via VibeProxy
    "vibeproxy-gemini-flash": {
        "big": "gemini-3-flash",                     # Gemini 3 Flash
        "small": "gemini-3-flash",
        "timeout": 15,
        "base_url": PROXY_URL,
        "api_key": "pass",
    },
    "vibeproxy-gemini-pro": {
        "big": "gemini-3-pro-preview",               # Gemini 3 Pro
        "small": "gemini-3-flash",
        "timeout": 15,
        "base_url": PROXY_URL,
        "api_key": "pass",
    },
    # OpenRouter direct for OSS-120 (free tier)
    # NOTE: Requires privacy settings at https://openrouter.ai/settings/privacy
    "openrouter-oss120": {
        "big": "openai/gpt-oss-120b:free",           # OSS 120B free via OpenRouter
        "small": "openai/gpt-oss-120b:free",         # Same for tool calls (free)
        "timeout": 30,                               # Allow more time for free tier
        "base_url": OPENROUTER_URL,
        "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "headers_extra": {                           # OpenRouter-specific headers
            "HTTP-Referer": "https://github.com/anthropics/claude-code",
            "X-Title": "claude-code-proxy-test",
        },
        "skip_reason": "Requires OpenRouter privacy settings (https://openrouter.ai/settings/privacy)",
    },
    # OpenRouter mimo-v2-flash - Xiaomi's fast free model with tool support
    "openrouter-mimo": {
        "big": "xiaomi/mimo-v2-flash:free",          # Mimo V2 Flash free
        "small": "xiaomi/mimo-v2-flash:free",        # Same for tool calls
        "timeout": 45,                               # Allow more time for free tier
        "base_url": PROXY_URL,                       # Via proxy to handle conversion
        "api_key": "pass",
    },
    # OpenRouter mimo-v2-flash via direct OpenRouter API
    "openrouter-mimo-direct": {
        "big": "xiaomi/mimo-v2-flash:free",
        "small": "xiaomi/mimo-v2-flash:free",
        "timeout": 45,
        "base_url": OPENROUTER_URL,
        "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "headers_extra": {
            "HTTP-Referer": "https://github.com/anthropics/claude-code",
            "X-Title": "claude-code-proxy-test",
        },
    },
    # OpenRouter Kimi-K2 - Moonshot's large free model
    "openrouter-kimi": {
        "big": "moonshotai/kimi-k2:free",            # Kimi K2 free (very capable)
        "small": "moonshotai/kimi-k2:free",          # Same for tools
        "timeout": 60,                               # Large model needs more time
        "base_url": PROXY_URL,
        "api_key": "pass",
    },
    # Hybrid: VibeProxy big model + Gemini Flash for tools
    "hybrid-sonnet-flash": {
        "big": "gemini-claude-sonnet-4-5-thinking",  # VibeProxy Sonnet thinking for main
        "small": "gemini-3-flash",                   # Gemini Flash for tool calls
        "timeout": 15,
        "base_url": PROXY_URL,
        "api_key": "pass",
    },
}

# API key is always "pass" - proxy sets real key based on provider
API_KEY = "pass"

# Default provider for single tests
DEFAULT_PROVIDER = "vibeproxy-gemini-claude-sonnet-thinking"


def is_openai_format(config: dict) -> bool:
    """Check if provider uses OpenAI format (not Anthropic)."""
    base_url = config.get("base_url", "")
    return "openrouter" in base_url


def test_health():
    """Test proxy health endpoint."""
    try:
        resp = urllib.request.urlopen(f"{PROXY_URL}/health", timeout=5)
        data = json.loads(resp.read().decode())
        return data.get("status") == "healthy", data
    except Exception as e:
        return False, str(e)


def test_simple_request(model: str = None, timeout: int = 15, config: dict = None):
    """Test simple API request."""
    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    config = config or PROVIDER_CONFIGS[DEFAULT_PROVIDER]
    model = model or config["small"]
    base_url = config.get("base_url", PROXY_URL)
    api_key = config.get("api_key", API_KEY)
    use_openai_format = is_openai_format(config)

    if use_openai_format:
        # OpenAI/OpenRouter format
        payload = json.dumps({
            "model": model,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say 'test passed' exactly"}]
        }).encode()
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    else:
        # Anthropic format
        payload = json.dumps({
            "model": model,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say 'test passed' exactly"}]
        }).encode()
        endpoint = f"{base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

    # Add extra headers if present
    if config.get("headers_extra"):
        headers.update(config["headers_extra"])

    req = urllib.request.Request(endpoint, data=payload, headers=headers)

    try:
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=timeout)
        duration = time.time() - start
        data = json.loads(resp.read().decode())

        content = ""
        if use_openai_format:
            # OpenAI format: choices[0].message.content
            if data.get("choices"):
                content = data["choices"][0].get("message", {}).get("content", "")
        else:
            # Anthropic format: content[0].text
            if data.get("content"):
                for block in data["content"]:
                    if block.get("type") == "text":
                        content = block.get("text", "")

        return True, {
            "model": data.get("model"),
            "requested_model": model,
            "content": content[:100],
            "usage": data.get("usage"),
            "duration": f"{duration:.1f}s"
        }, start_time

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return False, {"error": str(e), "status": e.code, "body": error_body[:200]}, start_time
    except Exception as e:
        return False, str(e), start_time


def test_tool_use(model: str = None, timeout: int = 15, config: dict = None):
    """Test API request with tool call."""
    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    config = config or PROVIDER_CONFIGS[DEFAULT_PROVIDER]
    model = model or config["small"]
    base_url = config.get("base_url", PROXY_URL)
    api_key = config.get("api_key", API_KEY)
    use_openai_format = is_openai_format(config)

    if use_openai_format:
        # OpenAI format
        payload = json.dumps({
            "model": model,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": "What is 25 * 4? Use the calculator tool."}],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Performs arithmetic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "Math expression"}
                        },
                        "required": ["expression"]
                    }
                }
            }]
        }).encode()
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    else:
        # Anthropic format
        payload = json.dumps({
            "model": model,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": "What is 25 * 4? Use the calculator tool."}],
            "tools": [{
                "name": "calculator",
                "description": "Performs arithmetic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"}
                    },
                    "required": ["expression"]
                }
            }]
        }).encode()
        endpoint = f"{base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

    if config.get("headers_extra"):
        headers.update(config["headers_extra"])

    req = urllib.request.Request(endpoint, data=payload, headers=headers)

    try:
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=timeout)
        duration = time.time() - start
        data = json.loads(resp.read().decode())

        tool_use = None
        stop_reason = None
        if use_openai_format:
            # OpenAI format: choices[0].message.tool_calls
            if data.get("choices"):
                choice = data["choices"][0]
                message = choice.get("message", {})
                tool_calls = message.get("tool_calls", [])
                if tool_calls:
                    tc = tool_calls[0]
                    func = tc.get("function", {})
                    tool_use = {
                        "name": func.get("name"),
                        "input": json.loads(func.get("arguments", "{}"))
                    }
                stop_reason = choice.get("finish_reason")
        else:
            # Anthropic format
            for block in data.get("content", []):
                if block.get("type") == "tool_use":
                    tool_use = {"name": block.get("name"), "input": block.get("input")}
                    break
            stop_reason = data.get("stop_reason")

        return True, {
            "model": data.get("model"),
            "requested_model": model,
            "tool_use": tool_use,
            "stop_reason": stop_reason,
            "duration": f"{duration:.1f}s"
        }, start_time

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return False, {"error": str(e), "status": e.code, "body": error_body[:200]}, start_time
    except Exception as e:
        return False, str(e), start_time


def _build_headers(config: dict) -> dict:
    """Build request headers for a provider config."""
    base_url = config.get("base_url", PROXY_URL)
    api_key = config.get("api_key", API_KEY)
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    if config.get("headers_extra"):
        headers.update(config["headers_extra"])
    if "openrouter" in base_url:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def test_multi_turn_tool_use(model: str = None, timeout: int = 15, config: dict = None):
    """Test full tool use cycle: request -> tool_use -> tool_result -> response."""
    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    config = config or PROVIDER_CONFIGS[DEFAULT_PROVIDER]
    model = model or config["small"]
    base_url = config.get("base_url", PROXY_URL)
    headers = _build_headers(config)

    # Step 1: Initial request with tool
    payload1 = json.dumps({
        "model": model,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": "What is 15 + 27? Use the calculator."}],
        "tools": [{
            "name": "calculator",
            "description": "Performs arithmetic calculations",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"}
                },
                "required": ["expression"]
            }
        }]
    }).encode()

    req1 = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=payload1,
        headers=headers
    )

    try:
        start = time.time()
        resp1 = urllib.request.urlopen(req1, timeout=timeout)
        data1 = json.loads(resp1.read().decode())
        duration1 = time.time() - start

        # Extract tool_use block
        tool_use_id = None
        tool_name = None
        tool_input = None
        for block in data1.get("content", []):
            if block.get("type") == "tool_use":
                tool_use_id = block.get("id")
                tool_name = block.get("name")
                tool_input = block.get("input")
                break

        if not tool_use_id:
            return False, {"error": "No tool_use in response", "response": data1}, start_time

        print(f"    Step 1: Got tool_use (id={tool_use_id[:12]}..., name={tool_name}) in {duration1:.1f}s")

        # Step 2: Send tool_result back
        payload2 = json.dumps({
            "model": model,
            "max_tokens": 200,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "What is 15 + 27? Use the calculator."}]},
                {"role": "assistant", "content": [
                    {"type": "tool_use", "id": tool_use_id, "name": tool_name, "input": tool_input}
                ]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tool_use_id, "content": "42"}
                ]}
            ],
            "tools": [{
                "name": "calculator",
                "description": "Performs arithmetic calculations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression to evaluate"}
                    },
                    "required": ["expression"]
                }
            }]
        }).encode()

        req2 = urllib.request.Request(
            f"{base_url}/v1/messages",
            data=payload2,
            headers=headers
        )

        start2 = time.time()
        resp2 = urllib.request.urlopen(req2, timeout=timeout)
        data2 = json.loads(resp2.read().decode())
        duration2 = time.time() - start2

        # Check for final text response
        final_text = ""
        has_duplicate_tool = False
        tool_count = 0
        for block in data2.get("content", []):
            if block.get("type") == "text":
                final_text = block.get("text", "")
            if block.get("type") == "tool_use":
                tool_count += 1

        if tool_count > 1:
            has_duplicate_tool = True

        print(f"    Step 2: Got response in {duration2:.1f}s")

        return True, {
            "step1_duration": f"{duration1:.1f}s",
            "step2_duration": f"{duration2:.1f}s",
            "total_duration": f"{duration1 + duration2:.1f}s",
            "tool_use_id": tool_use_id[:12] + "...",
            "final_text": final_text[:80] if final_text else "(no text)",
            "stop_reason": data2.get("stop_reason"),
            "duplicate_tools": has_duplicate_tool,
            "tool_count": tool_count
        }, start_time

    except urllib.error.URLError as e:
        return False, {"error": str(e)}, start_time
    except Exception as e:
        return False, {"error": str(e), "type": type(e).__name__}, start_time


def test_poem_file_creation(model: str = None, timeout: int = 15):
    """Test full Write tool cycle: request poem -> write_file tool -> verify completion."""
    import tempfile
    from pathlib import Path

    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    model = model or PROVIDER_CONFIGS[DEFAULT_PROVIDER]["small"]

    # Create temp workspace
    workspace = Path(tempfile.mkdtemp(prefix="proxy_poem_test_"))
    poem_file = workspace / "poem.txt"

    # Step 1: Ask model to write a poem using write_file tool
    payload1 = json.dumps({
        "model": model,
        "max_tokens": 500,
        "messages": [{"role": "user", "content": "Write a short 4-line poem about coding and save it to poem.txt using the write_file tool."}],
        "tools": [{
            "name": "write_file",
            "description": "Writes content to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write to"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }]
    }).encode()

    req1 = urllib.request.Request(
        f"{PROXY_URL}/v1/messages",
        data=payload1,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )

    try:
        start = time.time()
        resp1 = urllib.request.urlopen(req1, timeout=timeout)
        data1 = json.loads(resp1.read().decode())
        duration1 = time.time() - start

        # Extract write_file tool call
        tool_use_id = None
        tool_input = None
        poem_content = None
        for block in data1.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == "write_file":
                tool_use_id = block.get("id")
                tool_input = block.get("input", {})
                poem_content = tool_input.get("content", "")
                break

        if not tool_use_id:
            return False, {"error": "No write_file tool_use in response", "content": data1.get("content")}, start_time, None

        print(f"    Step 1: Got write_file tool call in {duration1:.1f}s")
        print(f"    Poem content: {poem_content[:60]}..." if len(poem_content) > 60 else f"    Poem content: {poem_content}")

        # Actually write the file to simulate tool execution
        poem_file.write_text(poem_content)

        # Step 2: Send tool_result back confirming write
        payload2 = json.dumps({
            "model": model,
            "max_tokens": 200,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "Write a short 4-line poem about coding and save it to poem.txt using the write_file tool."}]},
                {"role": "assistant", "content": [
                    {"type": "tool_use", "id": tool_use_id, "name": "write_file", "input": tool_input}
                ]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tool_use_id, "content": f"Successfully wrote {len(poem_content)} bytes to poem.txt"}
                ]}
            ],
            "tools": [{
                "name": "write_file",
                "description": "Writes content to a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            }]
        }).encode()

        req2 = urllib.request.Request(
            f"{PROXY_URL}/v1/messages",
            data=payload2,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01"
            }
        )

        start2 = time.time()
        resp2 = urllib.request.urlopen(req2, timeout=timeout)
        data2 = json.loads(resp2.read().decode())
        duration2 = time.time() - start2

        print(f"    Step 2: Got final response in {duration2:.1f}s")

        # Verify file exists and has content
        file_exists = poem_file.exists()
        file_content = poem_file.read_text() if file_exists else ""
        has_poem = len(file_content) > 10 and "\n" in file_content

        # Check stop reason
        stop_reason = data2.get("stop_reason")

        return True, {
            "step1_duration": f"{duration1:.1f}s",
            "step2_duration": f"{duration2:.1f}s",
            "total_duration": f"{duration1 + duration2:.1f}s",
            "file_exists": file_exists,
            "poem_lines": len(file_content.strip().split("\n")) if file_content else 0,
            "poem_bytes": len(file_content),
            "stop_reason": stop_reason,
            "file_path": str(poem_file)
        }, start_time, workspace

    except Exception as e:
        return False, {"error": str(e), "type": type(e).__name__}, start_time, workspace


def test_bash_tool_use(model: str = None, timeout: int = 15, config: dict = None):
    """Test Bash tool cycle - this is what caused infinite loops."""
    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    config = config or PROVIDER_CONFIGS[DEFAULT_PROVIDER]
    model = model or config["small"]
    base_url = config.get("base_url", PROXY_URL)
    headers = _build_headers(config)

    # Step 1: Ask model to run a bash command
    payload1 = json.dumps({
        "model": model,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": "List the current directory using the bash tool with 'ls -la'"}],
        "tools": [{
            "name": "bash",
            "description": "Executes a bash command",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"}
                },
                "required": ["command"]
            }
        }]
    }).encode()

    req1 = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=payload1,
        headers=headers
    )

    try:
        start = time.time()
        resp1 = urllib.request.urlopen(req1, timeout=timeout)
        data1 = json.loads(resp1.read().decode())
        duration1 = time.time() - start

        # Extract bash tool call
        tool_use_id = None
        tool_input = None
        command = None
        for block in data1.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == "bash":
                tool_use_id = block.get("id")
                tool_input = block.get("input", {})
                command = tool_input.get("command", "")
                break

        if not tool_use_id:
            return False, {"error": "No bash tool_use in response", "content": data1.get("content")}, start_time

        print(f"    Step 1: Got bash tool call in {duration1:.1f}s")
        print(f"    Command: {command}")

        # Step 2: Send tool_result back with fake ls output
        fake_ls_output = """total 8
drwxr-xr-x  3 user  staff   96 Dec 29 10:00 .
drwxr-xr-x  5 user  staff  160 Dec 29 09:00 ..
-rw-r--r--  1 user  staff  123 Dec 29 10:00 poem.txt"""

        payload2 = json.dumps({
            "model": model,
            "max_tokens": 200,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "List the current directory using the bash tool with 'ls -la'"}]},
                {"role": "assistant", "content": [
                    {"type": "tool_use", "id": tool_use_id, "name": "bash", "input": tool_input}
                ]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tool_use_id, "content": fake_ls_output}
                ]}
            ],
            "tools": [{
                "name": "bash",
                "description": "Executes a bash command",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            }]
        }).encode()

        req2 = urllib.request.Request(
            f"{base_url}/v1/messages",
            data=payload2,
            headers=headers
        )

        start2 = time.time()
        resp2 = urllib.request.urlopen(req2, timeout=timeout)
        data2 = json.loads(resp2.read().decode())
        duration2 = time.time() - start2

        print(f"    Step 2: Got final response in {duration2:.1f}s")

        # Check for loops - should NOT have another bash tool call
        tool_count = 0
        final_text = ""
        for block in data2.get("content", []):
            if block.get("type") == "tool_use":
                tool_count += 1
            if block.get("type") == "text":
                final_text = block.get("text", "")

        stop_reason = data2.get("stop_reason")

        # Step 3: Final corroboration - send follow-up to ensure no loop
        payload3 = json.dumps({
            "model": model,
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "List the current directory using the bash tool with 'ls -la'"}]},
                {"role": "assistant", "content": [
                    {"type": "tool_use", "id": tool_use_id, "name": "bash", "input": tool_input}
                ]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tool_use_id, "content": fake_ls_output}
                ]},
                {"role": "assistant", "content": data2.get("content", [])},
                {"role": "user", "content": "Confirm: did you complete the task without errors?"}
            ],
            "tools": [{
                "name": "bash",
                "description": "Executes a bash command",
                "input_schema": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"]
                }
            }]
        }).encode()

        req3 = urllib.request.Request(
            f"{base_url}/v1/messages",
            data=payload3,
            headers=headers
        )

        start3 = time.time()
        resp3 = urllib.request.urlopen(req3, timeout=timeout)
        data3 = json.loads(resp3.read().decode())
        duration3 = time.time() - start3

        print(f"    Step 3: Corroboration response in {duration3:.1f}s")

        # Final check - should end turn, not loop
        final_stop = data3.get("stop_reason")
        final_tool_count = sum(1 for b in data3.get("content", []) if b.get("type") == "tool_use")

        return True, {
            "step1_duration": f"{duration1:.1f}s",
            "step2_duration": f"{duration2:.1f}s",
            "step3_duration": f"{duration3:.1f}s",
            "total_duration": f"{duration1 + duration2 + duration3:.1f}s",
            "command": command,
            "step2_stop": stop_reason,
            "step3_stop": final_stop,
            "tool_count_step2": tool_count,
            "tool_count_step3": final_tool_count,
            "has_loop": final_tool_count > 0 and final_stop == "tool_use",
            "final_text": final_text[:60] if final_text else "(no text)"
        }, start_time

    except Exception as e:
        return False, {"error": str(e), "type": type(e).__name__}, start_time


def test_db_logging(start_time: str):
    """Verify DB logged requests since start_time."""
    if not DB_PATH.exists():
        return False, "DB not found"

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM api_requests WHERE timestamp >= ?
        """, (start_time,))
        count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT original_model, routed_model, status, input_tokens, output_tokens
            FROM api_requests WHERE timestamp >= ?
            ORDER BY timestamp DESC LIMIT 3
        """, (start_time,))
        rows = cursor.fetchall()
        conn.close()

        return count > 0, {"count": count, "recent": rows}

    except Exception as e:
        return False, str(e)


def run_provider_tests(provider_name: str, config: dict) -> list:
    """Run all tests for a specific provider."""
    results = []
    model = config["small"]  # Use small model for faster tests
    timeout = config["timeout"]
    base_url = config.get("base_url", PROXY_URL)

    # Check for missing API key
    api_key = config.get("api_key", "")
    if not api_key:
        print(f"\n  SKIP: No API key configured for {provider_name}")
        return [(f"{provider_name}/NoKey", False)], None

    print(f"  Base URL: {base_url}")

    # Simple request
    print(f"\n  [a] Simple Request ({model})...")
    ok, data, start_time = test_simple_request(model=model, timeout=timeout, config=config)
    print(f"      {'PASS' if ok else 'FAIL'}: {str(data)[:100]}...")
    results.append((f"{provider_name}/Simple", ok))

    # Tool use
    print(f"  [b] Tool Use...")
    ok, data, _ = test_tool_use(model=model, timeout=timeout, config=config)
    print(f"      {'PASS' if ok else 'FAIL'}: {str(data)[:100]}...")
    results.append((f"{provider_name}/ToolUse", ok))

    # Multi-turn (loop detection)
    print(f"  [c] Multi-Turn Tool (loop detection)...")
    ok, data, _ = test_multi_turn_tool_use(model=model, timeout=timeout, config=config)
    if ok and not data.get("duplicate_tools"):
        print(f"      PASS: no loops")
        results.append((f"{provider_name}/MultiTurn", True))
    else:
        print(f"      FAIL: {data}")
        results.append((f"{provider_name}/MultiTurn", False))

    # Bash tool (critical)
    print(f"  [d] Bash Tool (loop detection)...")
    ok, data, _ = test_bash_tool_use(model=model, timeout=timeout, config=config)
    if ok and not data.get("has_loop"):
        print(f"      PASS: no loops")
        results.append((f"{provider_name}/Bash", True))
    else:
        print(f"      FAIL: {data}")
        results.append((f"{provider_name}/Bash", False))

    return results, start_time


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", "-p", help="Test only this provider")
    parser.add_argument("--all", "-a", action="store_true", help="Test all providers")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  DIRECT PROXY TEST - MULTI-PROVIDER")
    print("=" * 60)

    # Health check
    print("\n[1] Health Check...")
    ok, data = test_health()
    print(f"    {'PASS' if ok else 'FAIL'}: {data}")
    if not ok:
        print("\n  Proxy not running. Start with:")
        print("  DEBUG_TRAFFIC_LOG=true TRACK_USAGE=true uv run python start_proxy.py")
        return 1

    all_results = []
    start_time = None

    # Determine which providers to test
    if args.provider:
        providers = {args.provider: PROVIDER_CONFIGS.get(args.provider)}
        if not providers[args.provider]:
            print(f"\n  Unknown provider: {args.provider}")
            print(f"  Available: {', '.join(PROVIDER_CONFIGS.keys())}")
            return 1
    elif args.all:
        providers = PROVIDER_CONFIGS
    else:
        # Default: just the default provider
        providers = {DEFAULT_PROVIDER: PROVIDER_CONFIGS[DEFAULT_PROVIDER]}

    # Test each provider
    for provider_name, config in providers.items():
        print(f"\n{'=' * 60}")
        print(f"  PROVIDER: {provider_name}")
        print(f"  Models: big={config['big']}, small={config['small']}")
        print(f"  Timeout: {config['timeout']}s")

        # Check if skipped
        if config.get("skip_reason"):
            print(f"  SKIPPED: {config['skip_reason']}")
            continue

        try:
            results, st = run_provider_tests(provider_name, config)
            all_results.extend(results)
            if not start_time:
                start_time = st
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results.append((f"{provider_name}/Error", False))

    # DB logging check
    if start_time:
        print(f"\n[DB] Logging Check...")
        ok, data = test_db_logging(start_time)
        print(f"    {'PASS' if ok else 'FAIL'}: {data}")
        all_results.append(("DB Logging", ok))

    # Summary
    passed = sum(1 for _, ok in all_results if ok)
    total = len(all_results)
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY: {passed}/{total} passed")
    for name, ok in all_results:
        print(f"    {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  {'PASS' if passed == total else 'FAIL'}")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
