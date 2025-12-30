"""
IDE Detector Module

Detects the source IDE from incoming requests to apply appropriate
tool name and parameter transformations.

Supported IDEs:
- Claude Code (Anthropic format)
- Antigravity (Anthropic format)
- Codex CLI (OpenAI format)
- Gemini CLI (OpenAI-compatible)
- Qwen Code (OpenAI-compatible)
- OpenCode (OpenAI format)
"""

from enum import Enum
from typing import Optional, Dict, Any


class IDE(str, Enum):
    """Supported IDE clients."""
    CLAUDE_CODE = "claude_code"
    ANTIGRAVITY = "antigravity"
    CODEX_CLI = "codex_cli"
    GEMINI_CLI = "gemini_cli"
    QWEN_CODE = "qwen_code"
    OPENCODE = "opencode"
    UNKNOWN = "unknown"


class APIFormat(str, Enum):
    """API format types."""
    ANTHROPIC = "anthropic"  # /v1/messages with input_schema
    OPENAI = "openai"        # /v1/chat/completions with parameters


# IDE metadata configuration
IDE_CONFIG = {
    IDE.CLAUDE_CODE.value: {
        "api_format": APIFormat.ANTHROPIC.value,
        "user_agent_patterns": ["claude", "anthropic"],
        "tool_prefix": "",  # Uses capitalized names: Bash, Read, Write
    },
    IDE.ANTIGRAVITY.value: {
        "api_format": APIFormat.ANTHROPIC.value,
        "user_agent_patterns": ["antigravity", "gemini-ide"],
        "tool_prefix": "",  # Same as Claude Code
    },
    IDE.CODEX_CLI.value: {
        "api_format": APIFormat.OPENAI.value,
        "user_agent_patterns": ["codex", "openai-codex"],
        "header_markers": ["x-codex-version", "x-openai-codex"],
        "tool_prefix": "",  # Uses snake_case: run_command, read_file
    },
    IDE.GEMINI_CLI.value: {
        "api_format": APIFormat.OPENAI.value,
        "user_agent_patterns": ["gemini-cli", "google-gemini"],
        "header_markers": ["x-gemini-cli"],
        "tool_prefix": "",  # Uses snake_case: shell, read_file
    },
    IDE.QWEN_CODE.value: {
        "api_format": APIFormat.OPENAI.value,
        "user_agent_patterns": ["qwen", "qwen-code"],
        "header_markers": ["x-qwen-code"],
        "tool_prefix": "",  # Uses snake_case: execute, read
    },
    IDE.OPENCODE.value: {
        "api_format": APIFormat.OPENAI.value,
        "user_agent_patterns": ["opencode", "go-opencode"],
        "header_markers": ["x-opencode-version"],
        "tool_prefix": "",  # Uses snake_case: execute, read
    },
}


def detect_ide_from_headers(headers: Dict[str, str]) -> str:
    """
    Detect IDE from request headers.
    
    Args:
        headers: Request headers dict
        
    Returns:
        IDE identifier string
    """
    user_agent = headers.get("user-agent", "").lower()
    
    # Check for specific header markers first (most reliable)
    for ide, config in IDE_CONFIG.items():
        header_markers = config.get("header_markers", [])
        for marker in header_markers:
            if marker.lower() in [h.lower() for h in headers.keys()]:
                return ide
    
    # Check User-Agent patterns
    for ide, config in IDE_CONFIG.items():
        patterns = config.get("user_agent_patterns", [])
        for pattern in patterns:
            if pattern.lower() in user_agent:
                return ide
    
    return IDE.UNKNOWN.value


def detect_ide_from_endpoint(path: str) -> str:
    """
    Detect IDE type from endpoint path.
    
    Args:
        path: Request URL path
        
    Returns:
        API format (anthropic or openai)
    """
    path_lower = path.lower()
    
    # Anthropic format uses /v1/messages
    if "/messages" in path_lower:
        return APIFormat.ANTHROPIC.value
    
    # OpenAI format uses /v1/chat/completions
    if "/chat/completions" in path_lower:
        return APIFormat.OPENAI.value
    
    # Default to Anthropic (our primary use case)
    return APIFormat.ANTHROPIC.value


def detect_ide_from_body(body: Dict[str, Any]) -> str:
    """
    Detect IDE from request body structure.
    
    Args:
        body: Request body dict
        
    Returns:
        IDE identifier or UNKNOWN
    """
    # Anthropic format has specific structure
    if "messages" in body:
        messages = body.get("messages", [])
        if messages and isinstance(messages, list):
            first_msg = messages[0] if messages else {}
            content = first_msg.get("content", "")
            
            # Anthropic uses nested content structure
            if isinstance(content, list):
                return IDE.CLAUDE_CODE.value
    
    # Check for tools structure
    tools = body.get("tools", [])
    if tools and isinstance(tools, list):
        first_tool = tools[0] if tools else {}
        
        # Anthropic uses input_schema
        if "input_schema" in first_tool:
            return IDE.CLAUDE_CODE.value
        
        # OpenAI uses function.parameters
        if "function" in first_tool:
            return IDE.CODEX_CLI.value  # Default OpenAI format
    
    return IDE.UNKNOWN.value


def detect_ide(
    headers: Optional[Dict[str, str]] = None,
    path: Optional[str] = None,
    body: Optional[Dict[str, Any]] = None
) -> str:
    """
    Detect the source IDE from request data.
    
    Priority:
    1. Specific headers (most reliable)
    2. User-Agent patterns
    3. Request body structure
    4. Endpoint path
    
    Args:
        headers: Request headers
        path: Request URL path
        body: Request body
        
    Returns:
        IDE identifier string
    """
    # Try headers first
    if headers:
        ide = detect_ide_from_headers(headers)
        if ide != IDE.UNKNOWN.value:
            return ide
    
    # Try body structure
    if body:
        ide = detect_ide_from_body(body)
        if ide != IDE.UNKNOWN.value:
            return ide
    
    # Infer from endpoint
    if path:
        api_format = detect_ide_from_endpoint(path)
        if api_format == APIFormat.ANTHROPIC.value:
            return IDE.CLAUDE_CODE.value  # Default Anthropic client
        elif api_format == APIFormat.OPENAI.value:
            return IDE.CODEX_CLI.value  # Default OpenAI client
    
    return IDE.UNKNOWN.value


def get_api_format(ide: str) -> str:
    """
    Get the API format for an IDE.
    
    Args:
        ide: IDE identifier
        
    Returns:
        API format (anthropic or openai)
    """
    config = IDE_CONFIG.get(ide, {})
    return config.get("api_format", APIFormat.OPENAI.value)


def is_anthropic_format(ide: str) -> bool:
    """Check if IDE uses Anthropic API format."""
    return get_api_format(ide) == APIFormat.ANTHROPIC.value


def is_openai_format(ide: str) -> bool:
    """Check if IDE uses OpenAI API format."""
    return get_api_format(ide) == APIFormat.OPENAI.value


def get_ide_info(ide: str) -> Dict[str, Any]:
    """
    Get full configuration for an IDE.
    
    Args:
        ide: IDE identifier
        
    Returns:
        IDE configuration dict
    """
    return IDE_CONFIG.get(ide, {
        "api_format": APIFormat.OPENAI.value,
        "user_agent_patterns": [],
        "tool_prefix": ""
    })
