"""
System prompt loader for custom model prompts.
Supports file-based loading and inline prompts.
"""

import os
from pathlib import Path
from typing import Optional


class SecurityError(Exception):
    """Raised when a security violation is detected (e.g., path traversal)."""
    pass


def load_system_prompt(prompt_source: str) -> str:
    """
    Load system prompt from various sources.

    Args:
        prompt_source: Can be:
            - "path:/path/to/file.txt" - Load from file
            - Direct text - Return as-is

    Returns:
        The loaded prompt text

    Raises:
        ValueError: If prompt_source is None
        FileNotFoundError: If file path doesn't exist
        RuntimeError: If file cannot be read
        SecurityError: If file path is unsafe (path traversal)
    """
    if prompt_source is None:
        raise ValueError("prompt_source cannot be None")

    if not prompt_source:
        return ""

    # Check if it's a file path
    if prompt_source.startswith("path:"):
        file_path = prompt_source[5:]  # Remove "path:" prefix

        # Security: Check for path traversal attempts
        try:
            # Define allowed base directory (project root or specific prompts directory)
            base_dir = Path(__file__).parent.parent.parent.resolve()
            file_path_resolved = Path(file_path).resolve()

            # Check if the resolved path is within the allowed base directory
            file_path_resolved.relative_to(base_dir)
        except (ValueError, OSError) as e:
            # ValueError: path is not relative to base_dir
            # OSError: path resolution failed
            raise SecurityError(f"Unsafe file path (path traversal attempt): {file_path}")

        try:
            with open(file_path_resolved, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                # Validate content length
                if len(content) > 50000:  # 50KB limit
                    raise ValueError(f"System prompt too long ({len(content)} chars). Max 50,000 characters.")

                if len(content) < 3:
                    raise ValueError(f"System prompt too short ({len(content)} chars). Minimum 3 characters.")

                return content

        except FileNotFoundError:
            raise FileNotFoundError(f"System prompt file not found: {file_path}")
        except UnicodeDecodeError as e:
            raise RuntimeError(f"File encoding error: {file_path}. Use UTF-8 encoding. {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error loading system prompt from {file_path}: {str(e)}")

    # Return as inline prompt
    # Validate inline prompt length
    if len(prompt_source) > 50000:
        raise ValueError(f"Inline system prompt too long ({len(prompt_source)} chars). Max 50,000 characters.")

    if len(prompt_source) < 3 and len(prompt_source) > 0:
        raise ValueError(f"Inline system prompt too short ({len(prompt_source)} chars). Minimum 3 characters.")

    return prompt_source


def get_model_system_prompt(model_size: str, config) -> Optional[str]:
    """
    Get the system prompt for a specific model size.

    Args:
        model_size: "big", "middle", or "small"
        config: Configuration object

    Returns:
        The system prompt text or None if not configured
    """
    if model_size.lower() == "big":
        if not config.enable_custom_big_prompt:
            return None
        # Try file first, then inline
        if config.big_system_prompt_file:
            return load_system_prompt(f"path:{config.big_system_prompt_file}")
        if config.big_system_prompt:
            return load_system_prompt(config.big_system_prompt)

    elif model_size.lower() == "middle":
        if not config.enable_custom_middle_prompt:
            return None
        if config.middle_system_prompt_file:
            return load_system_prompt(f"path:{config.middle_system_prompt_file}")
        if config.middle_system_prompt:
            return load_system_prompt(config.middle_system_prompt)

    elif model_size.lower() == "small":
        if not config.enable_custom_small_prompt:
            return None
        if config.small_system_prompt_file:
            return load_system_prompt(f"path:{config.small_system_prompt_file}")
        if config.small_system_prompt:
            return load_system_prompt(config.small_system_prompt)

    return None


def inject_system_prompt(messages: list, model_size: str, config) -> list:
    """
    Inject custom system prompt into messages if configured.

    Args:
        messages: List of message dictionaries
        model_size: "big", "middle", or "small"
        config: Configuration object

    Returns:
        Messages list with system prompt injected
    """
    system_prompt = get_model_system_prompt(model_size, config)

    if not system_prompt:
        return messages

    # Check if system message already exists
    has_system = any(msg.get("role") == "system" for msg in messages)

    if has_system:
        # Update existing system message
        for msg in messages:
            if msg.get("role") == "system":
                msg["content"] = system_prompt
                break
    else:
        # Prepend system message
        messages.insert(0, {
            "role": "system",
            "content": system_prompt
        })

    return messages
