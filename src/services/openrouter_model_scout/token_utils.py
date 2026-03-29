"""
Token estimation utilities for tracking API usage.
Simple estimation based on character count (rough approximation).
"""

import logging

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Roughly estimate number of tokens in text.
    Uses approximation: 1 token ≈ 4 characters for English text.
    For more accurate counts, would use tiktoken, but this is sufficient for tracking.
    """
    if not text:
        return 0
    return len(text) // 4


def estimate_prompt_tokens(models_json: str) -> int:
    """
    Estimate tokens in the API request (prompt to send to OpenRouter).
    In this case, we're not sending a prompt; we're making a GET request.
    But we can estimate response size for cost tracking.
    """
    # GET request to /models endpoint: no body, so prompt tokens are 0
    return 0


def estimate_response_tokens(response_text: str) -> int:
    """
    Estimate tokens in the API response (completion tokens in OpenRouter billing context).
    OpenRouter may bill on response size; we estimate for our own tracking.
    """
    return estimate_tokens(response_text)


def track_api_call(request_size: int, response_size: int) -> dict:
    """
    Create a token usage record for an API call.

    Args:
        request_size: Size of request payload in characters (0 for GET)
        response_size: Size of response body in characters

    Returns:
        dict with prompt_tokens, completion_tokens, total_tokens
    """
    prompt_tokens = estimate_prompt_tokens("")  # TODO: actual request body if needed
    completion_tokens = estimate_response_tokens("a" * response_size)

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
