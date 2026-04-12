"""
Custom Router Example
────────────────────
Drop a copy of this file anywhere and point ROUTER_CUSTOM_PATH at it:

    ROUTER_CUSTOM_PATH=config/my_router.py

The proxy calls route(request, config) before every request.
Return a model string to override the selected model, or None to keep it.

JavaScript variant (.js) is also supported — see custom_router.example.js.
"""


def route(request: dict, config: dict) -> str | None:
    """
    Args:
        request: The OpenAI-format request body (dict).
                 Keys: messages, model, stream, tools, thinking, ...
        config:  Current router config values (dict).
                 Keys: default, background, think, long_context, web_search, image.

    Returns:
        A model string like "provider/model-name" to use for this request,
        or None to fall through to the built-in routing logic.
    """

    # ── Example 1: Force a specific model for coding requests ──
    messages = request.get("messages", [])
    last_user = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    if isinstance(last_user, str):
        if any(kw in last_user.lower() for kw in ("write a function", "refactor", "debug")):
            return "qwen/qwen3-235b-a22b:free"

    # ── Example 2: Route long tool lists to a capable model ──
    if len(request.get("tools", [])) > 10:
        return "openai/gpt-oss-120b:free"

    # ── Example 3: Keep thinking requests on the configured think model ──
    if request.get("thinking", {}).get("type") == "enabled":
        return config.get("think") or None

    # Fall through — built-in routing takes over
    return None
