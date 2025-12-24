import os
import json
import sqlite3
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional

class AntigravityClient:
    """
    Antigravity API client for making requests to Google's internal daily-cloudcode-pa endpoint.
    Uses the OAuth token from Antigravity's VSCode state and the proprietary nested JSON payload format
    reverse-engineered from CLIProxyAPI.
    """
    
    def __init__(self):
        self.base_url = "https://daily-cloudcode-pa.sandbox.googleapis.com"
        # self.base_url = "https://cloudcode-pa.googleapis.com" # Prod URL fallback
        self.user_agent = "antigravity/1.11.5 darwin/arm64"
        self._token = None
        self._load_token()

    def _load_token(self):
        """Extracts the OAuth token from Antigravity's local SQLite database."""
        db_path = Path.home() / 'Library/Application Support/Antigravity/User/globalStorage/state.vscdb'
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key='antigravityAuthStatus'")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                data = json.loads(result[0])
                self._token = data.get('apiKey')
        except Exception as e:
            print(f"Error loading Antigravity token: {e}")

    def create_chat_completion(self, messages: List[Dict[str, str]], model: str = "gemini-3-pro-high", **kwargs) -> Dict[str, Any]:
        """
        Creates a chat completion using the Antigravity internal API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (defaults to gemini-3-pro-high)
            **kwargs: Additional generation config parameters
        """
        if not self._token:
            self._load_token()
            if not self._token:
                raise ValueError("No Antigravity token found. Please login to Antigravity.")

        # Convert standard messages to Antigravity "contents" format
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        # Build generation config
        generation_config = {
            "maxOutputTokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "topP": kwargs.get("top_p", 0.95),
            "topK": kwargs.get("top_k", 40),
        }

        # Construct payload with proprietary nested structure
        # Structure found from CLIProxyAPI: {"project":"", "request": {"contents":[]}, "model":"..."}
        payload = {
            "project": "",
            "model": model,
            "request": {
                "contents": contents,
                "generationConfig": generation_config
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }

        endpoint = "/v1internal:generateContent"
        url = f"{self.base_url}{endpoint}"
        
        # print(f"Sending request to {url}")
        # print(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            # Using verify=False as we found in prior steps that SSL certs might be an issue with some proxies,
            # though direct connection should work. Keeping it False for initial success.
            response = httpx.post(url, headers=headers, json=payload, timeout=60.0, verify=False)
            response.raise_for_status()
            
            result = response.json()
            return self._convert_response(result)
            
        except httpx.HTTPStatusError as e:
            print(f"Antigravity API Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

    def _convert_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts Antigravity response to OpenAI-compatible format."""
        
        # Unpack 'response' wrapper if present
        data = response_data
        if "response" in response_data:
            data = response_data["response"]
            
        content = ""
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate:
                content_obj = candidate["content"]
                if "parts" in content_obj:
                    parts = content_obj["parts"]
                    if parts:
                        content = "".join([p.get("text", "") for p in parts])

        return {
            "id": "antigravity-chat",
            "object": "chat.completion",
            "created": 0,
            "model": "antigravity-model",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
