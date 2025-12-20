"""Antigravity API client for making requests to Google's internal endpoint.

This module provides the HTTP client for making AI model requests
to the Antigravity/daily-cloudcode-pa.sandbox.googleapis.com endpoint.
"""

import json
import logging
import aiohttp
from typing import Dict, Any, Optional, AsyncIterator

from src.services.antigravity import get_antigravity_token, get_antigravity_auth

logger = logging.getLogger(__name__)

# Antigravity API endpoints
ANTIGRAVITY_BASE_URL = "https://daily-cloudcode-pa.sandbox.googleapis.com"


class AntigravityClient:
    """Client for Antigravity API (daily-cloudcode-pa.sandbox.googleapis.com)."""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with OAuth token."""
        token = get_antigravity_token()
        if not token:
            raise ValueError("No Antigravity OAuth token available. Log into Antigravity IDE first.")
        
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Claude-Code-Proxy/1.0"
        }
    
    async def create_chat_completion(
        self,
        messages: list,
        model: str = "Gemini 3 Pro (High)",
        max_tokens: int = 8192,
        temperature: float = 1.0,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Antigravity API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Antigravity model name (e.g., "Gemini 3 Pro (High)")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Response dict in OpenAI format
        """
        session = await self._get_session()
        headers = self._get_headers()
        
        # Convert OpenAI-style messages to Gemini-style contents
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                # Gemini uses systemInstruction separately
                system_instruction = {"parts": [{"text": content}]}
            else:
                # Map roles: user -> user, assistant -> model
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        # Build Gemini-style payload
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        
        endpoint = f"{ANTIGRAVITY_BASE_URL}/v1internal:streamGenerateContent"
        if not stream:
            endpoint = f"{ANTIGRAVITY_BASE_URL}/v1internal:generateContent"
        
        logger.info(f"Antigravity request: model={model}, contents={len(contents)}")
        
        try:
            async with session.post(
                endpoint,
                headers=headers,
                json=payload,
                ssl=False  # Disable SSL verification for testing
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Antigravity API error: {response.status} - {error_text}")
                    raise Exception(f"Antigravity API error: {response.status} - {error_text}")
                
                data = await response.json()
                
                # Convert to OpenAI-compatible format
                return self._convert_to_openai_format(data, model)
                
        except aiohttp.ClientError as e:
            logger.error(f"Antigravity connection error: {e}")
            raise
    
    async def create_chat_completion_stream(
        self,
        messages: list,
        model: str = "Gemini 3 Pro (High)",
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Create a streaming chat completion.
        
        Yields:
            Chunks in OpenAI SSE format
        """
        session = await self._get_session()
        headers = self._get_headers()
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value
        
        endpoint = f"{ANTIGRAVITY_BASE_URL}/v1internal:streamGenerateContent?alt=sse"
        
        logger.info(f"Antigravity stream request: model={model}")
        
        try:
            async with session.post(
                endpoint,
                headers=headers,
                json=payload,
                ssl=False
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Antigravity API error: {response.status} - {error_text}")
                
                # Parse SSE stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            yield self._convert_chunk_to_openai_format(data, model)
                        except json.JSONDecodeError:
                            continue
                            
        except aiohttp.ClientError as e:
            logger.error(f"Antigravity stream error: {e}")
            raise
    
    def _convert_to_openai_format(self, response: Dict, model: str) -> Dict[str, Any]:
        """Convert Antigravity response to OpenAI format."""
        # Extract text content - adjust based on actual response format
        content = ""
        if "candidates" in response and response["candidates"]:
            candidate = response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                content = "".join(p.get("text", "") for p in parts)
        elif "text" in response:
            content = response["text"]
        elif "content" in response:
            content = response["content"]
        
        return {
            "id": f"chatcmpl-antigravity-{id(response)}",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": response.get("usageMetadata", {}).get("promptTokenCount", 0),
                "completion_tokens": response.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                "total_tokens": response.get("usageMetadata", {}).get("totalTokenCount", 0)
            }
        }
    
    def _convert_chunk_to_openai_format(self, chunk: Dict, model: str) -> Dict[str, Any]:
        """Convert streaming chunk to OpenAI format."""
        content = ""
        if "candidates" in chunk and chunk["candidates"]:
            candidate = chunk["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                content = "".join(p.get("text", "") for p in parts)
        
        return {
            "id": f"chatcmpl-antigravity-stream",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {
                    "content": content
                },
                "finish_reason": None
            }]
        }
    
    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton instance
_client: Optional[AntigravityClient] = None


def get_antigravity_client() -> AntigravityClient:
    """Get or create the Antigravity client singleton."""
    global _client
    if _client is None:
        _client = AntigravityClient()
    return _client


async def is_antigravity_available() -> bool:
    """Check if Antigravity is available and token is valid."""
    auth = get_antigravity_auth()
    return auth.is_available()
