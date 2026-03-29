import threading
from typing import Dict, Optional, Tuple

# Behavior-driven cache for tool argument styles per provider/tool.
# Goal: avoid model-specific hardcoding by learning from observed responses.

_lock = threading.Lock()
_preferences: Dict[Tuple[str, str], str] = {}


def record_tool_argument_style(
    provider: Optional[str], tool_name: Optional[str], arguments: object
) -> None:
    """Record observed argument style for a tool (prompt vs command)."""
    if not provider or not tool_name or not isinstance(arguments, dict):
        return

    provider_key = provider.lower()
    tool_key = tool_name.lower()

    style = None
    if "prompt" in arguments and "command" not in arguments:
        style = "prompt"
    elif "command" in arguments and "prompt" not in arguments:
        style = "command"

    if style:
        with _lock:
            _preferences[(provider_key, tool_key)] = style


def get_tool_argument_style(
    provider: Optional[str], tool_name: Optional[str]
) -> Optional[str]:
    """Get observed argument style for a tool, if available."""
    if not provider or not tool_name:
        return None

    provider_key = provider.lower()
    tool_key = tool_name.lower()
    with _lock:
        return _preferences.get((provider_key, tool_key))
