"""
Universal Tool Mapper

Maps tool names and parameters between different IDE formats.
Enables any IDE to work with any backend provider through
canonical tool name normalization.

Supported mappings:
- Claude Code ↔ Codex CLI ↔ Gemini CLI ↔ Qwen Code ↔ OpenCode
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class ToolCategory(str, Enum):
    """Tool categories for organization."""
    SHELL = "shell"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    SEARCH = "search"
    NAVIGATION = "navigation"
    TASK = "task"
    WEB = "web"
    NOTEBOOK = "notebook"
    TODO = "todo"


# Canonical tool definitions with all IDE variants
# Format: canonical_name -> {ide_name: tool_name, params: {canonical: [variants]}}
TOOL_REGISTRY = {
    # ═══════════════════════════════════════════════════════════════
    # SHELL EXECUTION
    # ═══════════════════════════════════════════════════════════════
    "bash": {
        "category": ToolCategory.SHELL.value,
        "names": {
            "claude_code": "Bash",
            "antigravity": "Bash",
            "codex_cli": "run_command",
            "gemini_cli": "shell",
            "qwen_code": "execute",
            "opencode": "execute",
        },
        "params": {
            "command": ["prompt", "code", "cmd", "script", "input"],
            "timeout": ["timeout_ms", "time_limit"],
        }
    },
    "repl": {
        "category": ToolCategory.SHELL.value,
        "names": {
            "claude_code": "Repl",
            "antigravity": "Repl",
            "codex_cli": "run_code",
            "gemini_cli": "execute_code",
            "qwen_code": "run_code",
            "opencode": "run_code",
        },
        "params": {
            "command": ["code", "script", "prompt"],
        }
    },
    
    # ═══════════════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    "read": {
        "category": ToolCategory.FILE_READ.value,
        "names": {
            "claude_code": "Read",
            "antigravity": "Read",
            "codex_cli": "read_file",
            "gemini_cli": "read_file",
            "qwen_code": "read",
            "opencode": "read",
        },
        "params": {
            "file_path": ["path", "filename", "file", "filepath"],
            "start_line": ["start", "from_line", "line_start"],
            "end_line": ["end", "to_line", "line_end"],
        }
    },
    "write": {
        "category": ToolCategory.FILE_WRITE.value,
        "names": {
            "claude_code": "Write",
            "antigravity": "Write",
            "codex_cli": "write_file",
            "gemini_cli": "write_file",
            "qwen_code": "write",
            "opencode": "write",
        },
        "params": {
            "file_path": ["path", "filename", "file", "filepath"],
            "content": ["text", "data", "contents", "body"],
        }
    },
    "edit": {
        "category": ToolCategory.FILE_EDIT.value,
        "names": {
            "claude_code": "Edit",
            "antigravity": "Edit",
            "codex_cli": "patch_file",
            "gemini_cli": "edit_file",
            "qwen_code": "edit",
            "opencode": "edit",
        },
        "params": {
            "file_path": ["path", "file", "filename"],
            "old_text": ["original", "before", "search", "find"],
            "new_text": ["replacement", "after", "replace", "with"],
        }
    },
    "multiedit": {
        "category": ToolCategory.FILE_EDIT.value,
        "names": {
            "claude_code": "MultiEdit",
            "antigravity": "MultiEdit",
            "codex_cli": "multi_patch",
            "gemini_cli": "batch_edit",
            "qwen_code": "multiedit",
            "opencode": "multiedit",
        },
        "params": {
            "file_path": ["path", "file"],
            "edits": ["changes", "modifications", "patches"],
        }
    },
    
    # ═══════════════════════════════════════════════════════════════
    # SEARCH & NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    "grep": {
        "category": ToolCategory.SEARCH.value,
        "names": {
            "claude_code": "Grep",
            "antigravity": "Grep",
            "codex_cli": "search_files",
            "gemini_cli": "grep",
            "qwen_code": "search",
            "opencode": "search",
        },
        "params": {
            "pattern": ["query", "search", "regex", "term"],
            "path": ["directory", "dir", "folder", "root"],
            "include": ["include_pattern", "file_pattern"],
        }
    },
    "glob": {
        "category": ToolCategory.SEARCH.value,
        "names": {
            "claude_code": "Glob",
            "antigravity": "Glob",
            "codex_cli": "find_files",
            "gemini_cli": "glob",
            "qwen_code": "find",
            "opencode": "find",
        },
        "params": {
            "pattern": ["glob", "glob_pattern", "file_pattern"],
            "path": ["directory", "dir", "root"],
        }
    },
    "ls": {
        "category": ToolCategory.NAVIGATION.value,
        "names": {
            "claude_code": "LS",
            "antigravity": "LS",
            "codex_cli": "list_directory",
            "gemini_cli": "ls",
            "qwen_code": "list",
            "opencode": "list",
        },
        "params": {
            "path": ["directory", "dir", "folder"],
        }
    },
    
    # ═══════════════════════════════════════════════════════════════
    # TASK & AGENT
    # ═══════════════════════════════════════════════════════════════
    "task": {
        "category": ToolCategory.TASK.value,
        "names": {
            "claude_code": "Task",
            "antigravity": "Task",
            "codex_cli": "spawn_task",
            "gemini_cli": "create_task",
            "qwen_code": "task",
            "opencode": "task",
        },
        "params": {
            "description": ["prompt", "task", "instruction"],
            "subagent_type": ["agent_type", "type", "mode"],
        }
    },
    "agentdispatch": {
        "category": ToolCategory.TASK.value,
        "names": {
            "claude_code": "AgentDispatch",
            "antigravity": "AgentDispatch",
            "codex_cli": "dispatch_agent",
            "gemini_cli": "agent",
            "qwen_code": "dispatch",
            "opencode": "dispatch",
        },
        "params": {
            "agent_id": ["id", "agent"],
            "task": ["prompt", "instruction", "message"],
        }
    },
    
    # ═══════════════════════════════════════════════════════════════
    # WEB & BROWSER
    # ═══════════════════════════════════════════════════════════════
    "webfetch": {
        "category": ToolCategory.WEB.value,
        "names": {
            "claude_code": "WebFetch",
            "antigravity": "WebFetch",
            "codex_cli": "fetch_url",
            "gemini_cli": "browse",
            "qwen_code": "fetch",
            "opencode": "fetch",
        },
        "params": {
            "url": ["link", "href", "address", "uri"],
        }
    },
    "websearch": {
        "category": ToolCategory.WEB.value,
        "names": {
            "claude_code": "WebSearch",
            "antigravity": "WebSearch",
            "codex_cli": "web_search",
            "gemini_cli": "search_web",
            "qwen_code": "websearch",
            "opencode": "websearch",
        },
        "params": {
            "query": ["search", "q", "term", "keywords"],
        }
    },
    "browser": {
        "category": ToolCategory.WEB.value,
        "names": {
            "claude_code": "Browser",
            "antigravity": "Browser",
            "codex_cli": "browser",
            "gemini_cli": "open_browser",
            "qwen_code": "browser",
            "opencode": "browser",
        },
        "params": {
            "url": ["link", "address"],
            "action": ["command", "operation"],
        }
    },
    
    # ═══════════════════════════════════════════════════════════════
    # NOTEBOOK
    # ═══════════════════════════════════════════════════════════════
    "notebookedit": {
        "category": ToolCategory.NOTEBOOK.value,
        "names": {
            "claude_code": "NotebookEdit",
            "antigravity": "NotebookEdit",
            "codex_cli": "edit_notebook",
            "gemini_cli": "notebook_edit",
            "qwen_code": "notebookedit",
            "opencode": "notebookedit",
        },
        "params": {
            "notebook_path": ["path", "file", "notebook"],
            "cell_id": ["cell", "index", "cell_index"],
            "content": ["code", "source"],
        }
    },
    "notebookread": {
        "category": ToolCategory.NOTEBOOK.value,
        "names": {
            "claude_code": "NotebookRead",
            "antigravity": "NotebookRead",
            "codex_cli": "read_notebook",
            "gemini_cli": "notebook_read",
            "qwen_code": "notebookread",
            "opencode": "notebookread",
        },
        "params": {
            "notebook_path": ["path", "file", "notebook"],
        }
    },
    
    # ═══════════════════════════════════════════════════════════════
    # TODO MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    "todoread": {
        "category": ToolCategory.TODO.value,
        "names": {
            "claude_code": "TodoRead",
            "antigravity": "TodoRead",
            "codex_cli": "read_todos",
            "gemini_cli": "get_todos",
            "qwen_code": "todoread",
            "opencode": "todoread",
        },
        "params": {}
    },
    "todowrite": {
        "category": ToolCategory.TODO.value,
        "names": {
            "claude_code": "TodoWrite",
            "antigravity": "TodoWrite",
            "codex_cli": "write_todos",
            "gemini_cli": "set_todos",
            "qwen_code": "todowrite",
            "opencode": "todowrite",
        },
        "params": {
            "todos": ["tasks", "items", "list"],
        }
    },
}


def get_canonical_tool_name(tool_name: str) -> Optional[str]:
    """
    Get the canonical tool name from any IDE-specific name.
    
    Args:
        tool_name: Tool name from any IDE
        
    Returns:
        Canonical tool name or None if not found
    """
    tool_lower = tool_name.lower()
    
    # Check if it's already canonical
    if tool_lower in TOOL_REGISTRY:
        return tool_lower
    
    # Search through all variants
    for canonical, config in TOOL_REGISTRY.items():
        names = config.get("names", {})
        for ide_name in names.values():
            if ide_name.lower() == tool_lower:
                return canonical
    
    return None


def convert_tool_name(tool_name: str, target_ide: str) -> str:
    """
    Convert a tool name to the target IDE's format.
    
    Args:
        tool_name: Source tool name (any format)
        target_ide: Target IDE identifier
        
    Returns:
        Tool name in target IDE's format
    """
    canonical = get_canonical_tool_name(tool_name)
    if not canonical:
        return tool_name  # Return unchanged if not found
    
    config = TOOL_REGISTRY.get(canonical, {})
    names = config.get("names", {})
    return names.get(target_ide, tool_name)


def normalize_tool_params(
    tool_name: str, 
    params: Dict[str, Any],
    target_ide: str = "claude_code"
) -> Dict[str, Any]:
    """
    Normalize tool parameters to target IDE format.
    
    Args:
        tool_name: Tool name (any format)
        params: Parameter dict
        target_ide: Target IDE identifier
        
    Returns:
        Normalized parameter dict
    """
    canonical = get_canonical_tool_name(tool_name)
    if not canonical:
        return params  # Return unchanged if tool not found
    
    config = TOOL_REGISTRY.get(canonical, {})
    param_mappings = config.get("params", {})
    
    result = dict(params)  # Copy
    
    # Apply each canonical param mapping
    for canonical_param, variants in param_mappings.items():
        # Check if any variant exists in params
        for variant in variants:
            if variant in result and canonical_param not in result:
                result[canonical_param] = result.pop(variant)
                break
    
    return result


def get_tool_params_for_ide(
    canonical_tool: str,
    ide: str
) -> List[str]:
    """
    Get the expected parameter names for a tool in a specific IDE.
    
    Args:
        canonical_tool: Canonical tool name
        ide: IDE identifier
        
    Returns:
        List of expected parameter names
    """
    config = TOOL_REGISTRY.get(canonical_tool, {})
    param_mappings = config.get("params", {})
    
    # Return canonical param names (Claude Code format)
    if ide in ["claude_code", "antigravity"]:
        return list(param_mappings.keys())
    
    # For OpenAI-format IDEs, could customize, but canonical works
    return list(param_mappings.keys())


def list_all_tools() -> List[str]:
    """Get list of all canonical tool names."""
    return list(TOOL_REGISTRY.keys())


def get_tools_by_category(category: str) -> List[str]:
    """Get all tools in a category."""
    return [
        name for name, config in TOOL_REGISTRY.items()
        if config.get("category") == category
    ]


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get full information about a tool.
    
    Args:
        tool_name: Tool name (any format)
        
    Returns:
        Tool configuration dict or None
    """
    canonical = get_canonical_tool_name(tool_name)
    if not canonical:
        return None
    return TOOL_REGISTRY.get(canonical)


import re

def sanitize_function_name(name: str, max_length: int = 64) -> str:
    """
    Sanitize a function/tool name to be compatible with all providers.
    
    Addresses the INVALID_ARGUMENT errors that occur when tool names:
    - Start with dots, colons, dashes, or digits
    - Contain invalid characters
    - Exceed the maximum length (64 chars for most providers)
    
    This is equivalent to the SanitizeFunctionName utility in 
    CLIProxyAPI PR #803.
    
    Args:
        name: Original function/tool name
        max_length: Maximum allowed length (default 64)
        
    Returns:
        Sanitized function name safe for all providers
    """
    if not name:
        return "_unnamed"
    
    # Step 1: Remove invalid characters (keep only a-zA-Z0-9_.:-) 
    sanitized = re.sub(r'[^a-zA-Z0-9_.:\-]', '', name)
    
    # Step 2: Strip leading dots, colons, dashes
    sanitized = sanitized.lstrip('.:-')
    
    # Step 3: If starts with digit, prepend underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    
    # Step 4: If empty after sanitization, use placeholder
    if not sanitized:
        sanitized = '_tool'
    
    # Step 5: Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_tool_declarations(
    tools: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Sanitize all tool declarations in a list for provider compatibility.
    
    Args:
        tools: List of tool definitions (OpenAI function calling format)
        
    Returns:
        Tools with sanitized function names
    """
    if not tools:
        return tools
    
    result = []
    for tool in tools:
        tool_copy = dict(tool)
        if "function" in tool_copy:
            func = dict(tool_copy["function"])
            original_name = func.get("name", "")
            func["name"] = sanitize_function_name(original_name)
            tool_copy["function"] = func
        result.append(tool_copy)
    
    return result

