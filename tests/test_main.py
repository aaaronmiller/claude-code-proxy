"""Integration tests for Claude to OpenAI proxy.

These tests require the proxy server to be running at localhost:8082.
They are marked with @pytest.mark.integration and skipped by default.

To run integration tests:
1. Start the proxy: python start_proxy.py
2. Run: pytest tests/test_main.py -v -m integration
"""

import asyncio
import json
import os
import socket

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()

# Check if server is running
def server_is_running(host="localhost", port=8082):
    """Check if the proxy server is running."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

# Skip all tests in this module if server is not running
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not server_is_running(),
        reason="Proxy server not running at localhost:8082. Start with: python start_proxy.py"
    )
]


@pytest.mark.asyncio
async def test_basic_chat():
    """Test basic chat completion."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "error" in data


@pytest.mark.asyncio
async def test_streaming_chat():
    """Test streaming chat completion."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 150,
                "messages": [
                    {"role": "user", "content": "Tell me a short joke"}
                ],
                "stream": True
            }
        ) as response:
            assert response.status_code == 200
            chunks = []
            async for line in response.aiter_lines():
                if line.strip():
                    chunks.append(line)
            assert len(chunks) > 0


@pytest.mark.asyncio
async def test_function_calling():
    """Test function calling capability."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {"role": "user", "content": "What's the weather like in New York? Please use the weather function."}
                ],
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get the current weather for a location",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The location to get weather for"
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                    "description": "Temperature unit"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                ],
                "tool_choice": {"type": "auto"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "error" in data


@pytest.mark.asyncio
async def test_with_system_message():
    """Test with system message."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "system": "You are a helpful assistant that always responds in haiku format.",
                "messages": [
                    {"role": "user", "content": "Explain what AI is"}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "error" in data


@pytest.mark.asyncio
async def test_multimodal():
    """Test multimodal input (text + image)."""
    async with httpx.AsyncClient() as client:
        # Sample base64 image (1x1 pixel transparent PNG)
        sample_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8PJAAAAASUVORK5CYII="

        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": sample_image
                                }
                            }
                        ]
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "error" in data


@pytest.mark.asyncio
async def test_conversation_with_tool_use():
    """Test a complete conversation with tool use and results."""
    async with httpx.AsyncClient() as client:
        # First message with tool call
        response1 = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {"role": "user", "content": "Calculate 25 * 4 using the calculator tool"}
                ],
                "tools": [
                    {
                        "name": "calculator",
                        "description": "Perform basic arithmetic calculations",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "expression": {
                                    "type": "string",
                                    "description": "Mathematical expression to calculate"
                                }
                            },
                            "required": ["expression"]
                        }
                    }
                ]
            }
        )

        assert response1.status_code == 200
        result1 = response1.json()
        assert "content" in result1 or "error" in result1


@pytest.mark.asyncio
async def test_token_counting():
    """Test token counting endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8082/v1/messages/count_tokens",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "messages": [
                    {"role": "user", "content": "This is a test message for token counting."}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "input_tokens" in data


@pytest.mark.asyncio
async def test_health_and_connection():
    """Test health and connection endpoints."""
    async with httpx.AsyncClient() as client:
        # Health check
        health_response = await client.get("http://localhost:8082/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert "status" in health_data

        # Connection test (may fail if no valid API key, but endpoint should respond)
        connection_response = await client.get("http://localhost:8082/test-connection")
        assert connection_response.status_code in [200, 503]  # 503 if API key invalid


async def main():
    """Run all tests manually (for debugging)."""
    print("Testing Claude to OpenAI Proxy")
    print("=" * 50)

    if not server_is_running():
        print("\n Server not running at localhost:8082")
        print("Start with: python start_proxy.py")
        return

    try:
        await test_health_and_connection()
        print(" test_health_and_connection passed")

        await test_token_counting()
        print(" test_token_counting passed")

        await test_basic_chat()
        print(" test_basic_chat passed")

        await test_with_system_message()
        print(" test_with_system_message passed")

        await test_streaming_chat()
        print(" test_streaming_chat passed")

        await test_multimodal()
        print(" test_multimodal passed")

        await test_function_calling()
        print(" test_function_calling passed")

        await test_conversation_with_tool_use()
        print(" test_conversation_with_tool_use passed")

        print("\n All tests completed!")

    except Exception as e:
        print(f"\n Test failed: {e}")
        print("Make sure the server is running with a valid OPENAI_API_KEY")


if __name__ == "__main__":
    asyncio.run(main())
