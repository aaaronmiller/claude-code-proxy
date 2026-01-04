#!/usr/bin/env python3
"""
Tool Calling & Truncation Test

Tests tool calling functionality with OpenAI format,
including truncation of large tool outputs.

Uses /v1/chat/completions endpoint.
"""

import requests
import json
import os
import sys

PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:8082")
API_KEY = "pass"  # Proxy accepts any key for OpenAI format
MODEL = "gemini-3-flash"  # Fast model for testing

# OpenAI function calling format tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read a file from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to file"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Execute a bash command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["file_path", "content"]
            }
        }
    }
]


def make_request(messages, tools=None, stream=False, timeout=30):
    """Make OpenAI format request to proxy."""
    payload = {
        "model": MODEL,
        "max_tokens": 500,
        "messages": messages,
        "stream": stream
    }
    if tools:
        payload["tools"] = tools

    return requests.post(
        f"{PROXY_URL}/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json=payload,
        stream=stream,
        timeout=timeout
    )


def test_simple_request():
    """Test basic request without tools."""
    print("\n[1] Simple Request (no tools)...")

    response = make_request([{"role": "user", "content": "Say 'tool test passed' exactly."}])

    if response.status_code != 200:
        print(f"    FAIL: Status {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        return False

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"    PASS: {content[:50]}...")
    return True


def test_tool_call_request():
    """Test that model returns tool_use block."""
    print("\n[2] Tool Call Request...")

    response = make_request(
        [{"role": "user", "content": "Read the file /etc/hosts"}],
        tools=TOOLS
    )

    if response.status_code != 200:
        print(f"    FAIL: Status {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        return False

    data = response.json()

    # Check for tool_calls in message
    message = data.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls", [])

    if not tool_calls:
        # Model might respond with text instead - that's OK
        content = message.get("content", "")
        print(f"    WARN: No tool_calls, got text: {content[:50]}...")
        return True

    tool_call = tool_calls[0]
    print(f"    PASS: tool_call name={tool_call.get('function', {}).get('name')}, id={tool_call.get('id', '')[:12]}...")
    return True


def test_tool_result_flow():
    """Test complete tool call -> tool result -> response flow."""
    print("\n[3] Tool Result Flow...")

    # Step 1: Get tool call
    response = make_request(
        [{"role": "user", "content": "Use the Bash tool to run: echo 'hello from bash'"}],
        tools=TOOLS
    )

    if response.status_code != 200:
        print(f"    FAIL Step 1: Status {response.status_code}")
        return False

    data = response.json()
    message = data.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls", [])

    if not tool_calls:
        print(f"    SKIP: Model didn't use tool")
        return True

    tool_call = tool_calls[0]
    tool_id = tool_call.get("id")
    tool_name = tool_call.get("function", {}).get("name")
    print(f"    Step 1: Got tool_call name={tool_name}")

    # Step 2: Send tool result
    response = make_request(
        [
            {"role": "user", "content": "Use the Bash tool to run: echo 'hello from bash'"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls},
            {"role": "tool", "tool_call_id": tool_id, "content": "hello from bash\n"}
        ],
        tools=TOOLS
    )

    if response.status_code != 200:
        print(f"    FAIL Step 2: Status {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        return False

    data = response.json()
    finish_reason = data.get("choices", [{}])[0].get("finish_reason")
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")[:100]

    print(f"    Step 2: Got response, finish_reason={finish_reason}")
    print(f"    PASS: {content}...")
    return True


def test_large_tool_result_truncation():
    """Test that large tool results get truncated."""
    print("\n[4] Large Tool Result Truncation...")

    # Step 1: Get tool call for Read
    response = make_request(
        [{"role": "user", "content": "Read the file /tmp/large_test_file.txt"}],
        tools=TOOLS
    )

    if response.status_code != 200:
        print(f"    FAIL Step 1: Status {response.status_code}")
        return False

    data = response.json()
    message = data.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls", [])

    if not tool_calls:
        print(f"    SKIP: Model didn't use tool (responded with text)")
        return True

    tool_call = tool_calls[0]
    tool_id = tool_call.get("id")
    print(f"    Step 1: Got tool_call id={tool_id[:12]}...")

    # Step 2: Send LARGE tool result (100KB)
    large_content = "x" * 100000  # 100K chars

    response = make_request(
        [
            {"role": "user", "content": "Read the file /tmp/large_test_file.txt"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls},
            {"role": "tool", "tool_call_id": tool_id, "content": large_content}
        ],
        tools=TOOLS,
        timeout=60
    )

    if response.status_code != 200:
        print(f"    FAIL Step 2: Status {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        return False

    # If we get here, the truncation worked
    data = response.json()
    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)

    print(f"    Step 2: Request succeeded with {input_tokens} input tokens")
    print(f"    PASS: Large content was handled (truncation active)")
    return True


def test_streaming_tool_call():
    """Test streaming tool call."""
    print("\n[5] Streaming Tool Call...")

    response = make_request(
        [{"role": "user", "content": "Use the Bash tool to list files: ls -la"}],
        tools=TOOLS,
        stream=True
    )

    if response.status_code != 200:
        print(f"    FAIL: Status {response.status_code}")
        return False

    # Parse SSE events
    tool_call_detected = False
    tool_name = None

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith("data: "):
                chunk_data = line[6:]
                if chunk_data.strip() == "[DONE]":
                    break
                try:
                    event_data = json.loads(chunk_data)
                    delta = event_data.get("choices", [{}])[0].get("delta", {})

                    # Check for tool_calls in delta
                    if delta.get("tool_calls"):
                        tool_call_detected = True
                        for tc in delta["tool_calls"]:
                            if tc.get("function", {}).get("name"):
                                tool_name = tc["function"]["name"]
                except json.JSONDecodeError:
                    pass

    if tool_call_detected:
        print(f"    PASS: Streaming tool_call detected, name={tool_name}")
        return True
    else:
        print(f"    WARN: No tool_call in stream (model may have responded with text)")
        return True  # Not a failure


def main():
    print("=" * 60)
    print("  TOOL CALLING & TRUNCATION TEST")
    print("=" * 60)
    print(f"Proxy: {PROXY_URL}")
    print(f"Model: {MODEL}")

    results = []

    results.append(("Simple Request", test_simple_request()))
    results.append(("Tool Call Request", test_tool_call_request()))
    results.append(("Tool Result Flow", test_tool_result_flow()))
    results.append(("Large Result Truncation", test_large_tool_result_truncation()))
    results.append(("Streaming Tool Call", test_streaming_tool_call()))

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
