"""
Rate limiter for tracking RPM/TPM across providers and models dynamically.
"""

import time
import logging
import asyncio
import httpx
import json
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RateLimiter:
    """Tracks token and request rates per model/provider to enable intelligent routing."""

    def __init__(self):
        # Dictionary structure: { "model_name": {"rpm_limit": int, "tpm_limit": int, "requests": [], "tokens": []} }
        self._limits: Dict[str, Dict] = {}
        self._provider_status: Dict[str, Dict] = {}
        self._fetching: set = set()
        
    def is_unknown(self, model_name: str) -> bool:
        """Check if limits for this model are currently unknown."""
        return model_name not in self._limits
        
    async def fetch_limits_bg(self, model_name: str, api_key: str, base_url: str):
        """Make a minimal background request to fetch rate limits from headers."""
        if not api_key or model_name in self._fetching:
            return
            
        self._fetching.add(model_name)
        try:
            logger.debug(f"[RateLimiter] Fetching limits for {model_name} in background...")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            # Make a tiny request (max_tokens=1) just to get the headers
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1
            }
            url = f"{base_url.rstrip('/')}/chat/completions"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                # We don't care if it's 200 or 400 or 429, headers are usually there
                self.update_from_headers(model_name, response.headers)
        except Exception as e:
            logger.debug(f"[RateLimiter] Failed to fetch limits for {model_name}: {e}")
        finally:
            self._fetching.discard(model_name)

    def update_from_headers(self, model_name: str, headers: dict):
        """
        Update the known limits for a model based on HTTP response headers.
        Standard headers checked: x-ratelimit-limit-requests, x-ratelimit-remaining-requests.
        """
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # OpenRouter and OpenAI standard rate limit headers
        rpm_limit = headers_lower.get('x-ratelimit-limit-requests')
        rpm_remaining = headers_lower.get('x-ratelimit-remaining-requests')
        tpm_limit = headers_lower.get('x-ratelimit-limit-tokens')
        tpm_remaining = headers_lower.get('x-ratelimit-remaining-tokens')

        if rpm_limit or tpm_limit:
            if model_name not in self._limits:
                self._limits[model_name] = {"rpm_limit": 50, "tpm_limit": 100000, "requests": [], "tokens": []}
            
            if rpm_limit and str(rpm_limit).isdigit():
                self._limits[model_name]["rpm_limit"] = int(rpm_limit)
            if tpm_limit and str(tpm_limit).isdigit():
                self._limits[model_name]["tpm_limit"] = int(tpm_limit)
                
            if model_name not in self._provider_status:
                self._provider_status[model_name] = {"reset_time": 0}
                
            if rpm_remaining and str(rpm_remaining).isdigit():
                self._provider_status[model_name]["rpm_remaining"] = int(rpm_remaining)
            if tpm_remaining and str(tpm_remaining).isdigit():
                self._provider_status[model_name]["tpm_remaining"] = int(tpm_remaining)
                
            self._provider_status[model_name]["last_updated"] = time.time()
            logger.debug(f"[RateLimiter] Updated limits for {model_name}: RPM={rpm_limit}, TPM={tpm_limit}")

    def record_request(self, model_name: str, tokens: int = 0):
        """Record a successful or attempted request to update local sliding windows."""
        now = time.time()
        if model_name not in self._limits:
            self._limits[model_name] = {"rpm_limit": 50, "tpm_limit": 100000, "requests": [], "tokens": []}
            
        self._limits[model_name]["requests"].append(now)
        if tokens > 0:
            self._limits[model_name]["tokens"].append((now, tokens))
            
        # Also decrement the provider status if we have it
        if model_name in self._provider_status:
            if "rpm_remaining" in self._provider_status[model_name]:
                self._provider_status[model_name]["rpm_remaining"] = max(0, self._provider_status[model_name]["rpm_remaining"] - 1)
            if "tpm_remaining" in self._provider_status[model_name]:
                self._provider_status[model_name]["tpm_remaining"] = max(0, self._provider_status[model_name]["tpm_remaining"] - tokens)

    def _cleanup_sliding_window(self, model_name: str, now: float):
        """Remove events older than 60 seconds from the sliding window."""
        if model_name not in self._limits:
            return
            
        cutoff = now - 60.0
        self._limits[model_name]["requests"] = [t for t in self._limits[model_name]["requests"] if t > cutoff]
        self._limits[model_name]["tokens"] = [(t, v) for (t, v) in self._limits[model_name]["tokens"] if t > cutoff]

    def get_available_quota_score(self, model_name: str) -> float:
        """
        Returns a score from 0.0 to 1.0 indicating how much of the rate limit is available.
        1.0 means fully available, 0.0 means exhausted.
        """
        now = time.time()
        
        # Check explicit provider status first
        if model_name in self._provider_status and model_name in self._limits:
            status = self._provider_status[model_name]
            # If the provider explicitly told us we have 0 remaining, and it hasn't been a minute yet, score is 0
            if "rpm_remaining" in status and status["rpm_remaining"] <= 0:
                if now - status.get("last_updated", 0) < 60:
                    return 0.0
            if "tpm_remaining" in status and status["tpm_remaining"] <= 0:
                if now - status.get("last_updated", 0) < 60:
                    return 0.0
                    
            # If we know the limit and remaining, calculate true percentage
            rpm_limit = self._limits[model_name].get("rpm_limit", 50)
            if "rpm_remaining" in status and rpm_limit > 0:
                return float(status["rpm_remaining"]) / rpm_limit

        # Fallback to sliding window if we don't have header limits yet
        self._cleanup_sliding_window(model_name, now)
        
        if model_name not in self._limits:
            # If unknown, assume 1.0 so we try it at least once to get headers
            return 1.0
            
        limits = self._limits[model_name]
        rpm_limit = limits["rpm_limit"]
        
        current_rpm = len(limits["requests"])
        
        if rpm_limit <= 0:
            return 1.0
            
        available_pct = max(0.0, 1.0 - (current_rpm / rpm_limit))
        return available_pct
        
    def set_limit(self, model_name: str, rpm: int, tpm: int = 100000):
        """Manually override or set a limit."""
        if model_name not in self._limits:
            self._limits[model_name] = {"rpm_limit": rpm, "tpm_limit": tpm, "requests": [], "tokens": []}
        else:
            self._limits[model_name]["rpm_limit"] = rpm
            self._limits[model_name]["tpm_limit"] = tpm

# Global instance
rate_limiter = RateLimiter()
