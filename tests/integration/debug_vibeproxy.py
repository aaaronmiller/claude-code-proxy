import sys
import os
import asyncio
import httpx
import logging
from pprint import pprint

# Set up path to import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.services.antigravity import AntigravityAuth

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("vibeproxy_diag")

async def test_vibeproxy():
    print("\n--- DIAGNOSTIC: VibeProxy Connection & Auth ---\n")
    
    # 1. Test Token Retrieval (Stress Test)
    print("1. Fetching Antigravity Token (Stress Test - 50 iterations)...")
    auth = AntigravityAuth()
    
    for i in range(50):
        try:
            token = auth.get_token(force_refresh=(i % 10 == 0)) # Force refresh every 10th time
            if not token:
                print(f"❌ Iteration {i}: Token retrieval returned None")
                break
            if i % 10 == 0:
                print(f"   Iteration {i}: OK")
        except Exception as e:
            print(f"❌ Iteration {i}: Failed with {e}")
            break
    else:
        print("✅ All 50 iterations passed.")

    # 2. Test Connection to VibeProxy (Port 8317)
    api_url = "http://127.0.0.1:8317/v1/chat/completions"
    TEST_MODEL = "gemini-3-flash"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Test payload for Gemini 3 Flash
    # payload = {"model": "google/gemini-3-flash-preview", "messages": [{"role": "user", "content": "Hello"}]}
    payload = {
        "model": TEST_MODEL,
        "messages": [
            {"role": "user", "content": "Write a python script to print hello world to a file."}
        ],
        "stream": True,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                }
            }
        ]
    }

    try:
        print(f"\nSending request to {api_url}...")
        print(f"Model: {TEST_MODEL}")
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", api_url, headers=headers, json=payload, timeout=30.0) as response:
                print(f"Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_body = await response.aread()
                    print(f"Error Body: {error_body.decode()}")
                    return

                print("Streaming response:")
                async for chunk in response.aiter_bytes():
                    if chunk:
                        print(f"Chunk: {len(chunk)} bytes")
                        # Try to decode if it looks like text
                        try:
                            print(chunk.decode('utf-8')[:100] + "...")
                        except:
                            pass

    except httpx.ConnectError:
        print("❌ Connection Refused: Is VibeProxy (Antigravity IDE) running on port 8317?")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_vibeproxy())
