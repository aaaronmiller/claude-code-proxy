"""Tests for normalize_tool_arguments() type coercion and streaming fixes.

Covers all integer-typed parameters that Gemini may return as strings,
causing InputValidationError in Claude Code CLI.

Parameters covered:
- Bash/Repl: timeout
- Read: offset, limit
- NotebookEdit: cell_number
"""

import pytest
from src.services.conversion.response_converter import (
    normalize_tool_arguments,
    streaming_transform_partial,
)


# ============================================================
# Bash/Repl: timeout coercion
# ============================================================

class TestBashTimeoutCoercion:
    """Bash tool timeout: string → int coercion."""

    def test_timeout_string_coerced_to_int(self):
        args = {"command": "ls -la", "timeout": "120"}
        result = normalize_tool_arguments("Bash", args, provider="gemini")
        assert result["timeout"] == 120
        assert isinstance(result["timeout"], int)

    def test_timeout_already_int_unchanged(self):
        args = {"command": "ls -la", "timeout": 120}
        result = normalize_tool_arguments("Bash", args, provider="gemini")
        assert result["timeout"] == 120
        assert isinstance(result["timeout"], int)

    def test_timeout_invalid_string_left_unchanged(self):
        args = {"command": "ls -la", "timeout": "forever"}
        result = normalize_tool_arguments("Bash", args, provider="gemini")
        assert result["timeout"] == "forever"  # graceful pass-through

    def test_timeout_absent_no_error(self):
        args = {"command": "ls -la"}
        result = normalize_tool_arguments("Bash", args, provider="gemini")
        assert "timeout" not in result

    def test_repl_timeout_string_coerced(self):
        args = {"command": "print('hi')", "timeout": "30"}
        result = normalize_tool_arguments("Repl", args, provider="gemini")
        assert result["timeout"] == 30
        assert isinstance(result["timeout"], int)

    def test_prompt_rename_and_timeout_coercion_combined(self):
        """Gemini sends both wrong param name AND wrong type."""
        args = {"prompt": "echo hello", "timeout": "60"}
        result = normalize_tool_arguments("Bash", args, provider="gemini")
        assert result["command"] == "echo hello"
        assert "prompt" not in result
        assert result["timeout"] == 60
        assert isinstance(result["timeout"], int)


# ============================================================
# Read: offset/limit coercion
# ============================================================

class TestReadNumericCoercion:
    """Read tool offset/limit: string → int coercion."""

    def test_offset_string_coerced_to_int(self):
        args = {"file_path": "/foo/bar.py", "offset": "10"}
        result = normalize_tool_arguments("Read", args, provider="gemini")
        assert result["offset"] == 10
        assert isinstance(result["offset"], int)

    def test_limit_string_coerced_to_int(self):
        args = {"file_path": "/foo/bar.py", "limit": "50"}
        result = normalize_tool_arguments("Read", args, provider="gemini")
        assert result["limit"] == 50
        assert isinstance(result["limit"], int)

    def test_offset_and_limit_both_coerced(self):
        args = {"file_path": "/foo/bar.py", "offset": "10", "limit": "50"}
        result = normalize_tool_arguments("Read", args, provider="gemini")
        assert result["offset"] == 10
        assert result["limit"] == 50

    def test_offset_already_int_unchanged(self):
        args = {"file_path": "/foo/bar.py", "offset": 10}
        result = normalize_tool_arguments("Read", args, provider="gemini")
        assert result["offset"] == 10
        assert isinstance(result["offset"], int)

    def test_offset_invalid_string_left_unchanged(self):
        args = {"file_path": "/foo/bar.py", "offset": "beginning"}
        result = normalize_tool_arguments("Read", args, provider="gemini")
        assert result["offset"] == "beginning"

    def test_read_light_normalize_coercion(self):
        """OpenRouter also coerces Read numeric params."""
        args = {"file_path": "/foo/bar.py", "offset": "5", "limit": "100"}
        result = normalize_tool_arguments("Read", args, provider="openrouter")
        assert result["offset"] == 5
        assert result["limit"] == 100

    def test_path_rename_and_offset_coercion_combined(self):
        """Gemini sends wrong param name AND wrong type simultaneously."""
        args = {"path": "/foo/bar.py", "offset": "20", "limit": "30"}
        result = normalize_tool_arguments("Read", args, provider="gemini")
        assert result["file_path"] == "/foo/bar.py"
        assert "path" not in result
        assert result["offset"] == 20
        assert result["limit"] == 30


# ============================================================
# NotebookEdit: cell_number coercion
# ============================================================

class TestNotebookEditCoercion:
    """NotebookEdit cell_number: string → int coercion."""

    def test_cell_number_string_coerced(self):
        args = {"notebook_path": "nb.ipynb", "cell_number": "3", "content": "x=1"}
        result = normalize_tool_arguments("NotebookEdit", args, provider="gemini")
        assert result["cell_number"] == 3
        assert isinstance(result["cell_number"], int)

    def test_cell_number_already_int_unchanged(self):
        args = {"notebook_path": "nb.ipynb", "cell_number": 3, "content": "x=1"}
        result = normalize_tool_arguments("NotebookEdit", args, provider="gemini")
        assert result["cell_number"] == 3

    def test_cell_number_absent_no_error(self):
        args = {"notebook_path": "nb.ipynb", "content": "x=1"}
        result = normalize_tool_arguments("NotebookEdit", args, provider="gemini")
        assert "cell_number" not in result


# ============================================================
# Light normalization (OpenRouter)
# ============================================================

class TestLightNormalizeTimeout:
    """Light normalization path also coerces timeout."""

    def test_light_timeout_coercion(self):
        args = {"command": "ls", "timeout": "90"}
        result = normalize_tool_arguments("Bash", args, provider="openrouter")
        assert result["timeout"] == 90
        assert isinstance(result["timeout"], int)

    def test_light_timeout_already_int(self):
        args = {"command": "ls", "timeout": 90}
        result = normalize_tool_arguments("Bash", args, provider="openrouter")
        assert result["timeout"] == 90


# ============================================================
# No normalization (openai / azure)
# ============================================================

class TestNoNormalizeTimeout:
    """Providers with NONE normalization should pass through unchanged."""

    def test_openai_no_coercion(self):
        args = {"command": "ls", "timeout": "120"}
        result = normalize_tool_arguments("Bash", args, provider="openai")
        # Should be unchanged — openai gets NormalizationLevel.NONE
        assert result["timeout"] == "120"


# ============================================================
# Streaming path
# ============================================================

class TestStreamingNumericCoercion:
    """streaming_transform_partial() regex fix for all numeric params."""

    # --- Bash ---
    def test_streaming_bash_timeout_string_to_number(self):
        partial = '{"command":"ls -la","timeout":"120"}'
        result = streaming_transform_partial(partial, "Bash", provider="gemini")
        assert '"timeout":120' in result
        assert '"timeout":"120"' not in result

    def test_streaming_bash_timeout_already_number(self):
        partial = '{"command":"ls","timeout":120}'
        result = streaming_transform_partial(partial, "Bash", provider="gemini")
        assert '"timeout":120' in result

    def test_streaming_bash_prompt_to_command_still_works(self):
        partial = '{"prompt":"echo hi","timeout":"30"}'
        result = streaming_transform_partial(partial, "Bash", provider="gemini")
        assert '"command":' in result
        assert '"prompt":' not in result
        assert '"timeout":30' in result

    # --- Read ---
    def test_streaming_read_offset_string_to_number(self):
        partial = '{"file_path":"a.py","offset":"10","limit":"50"}'
        result = streaming_transform_partial(partial, "Read", provider="gemini")
        assert '"offset":10' in result
        assert '"limit":50' in result
        assert '"offset":"10"' not in result

    def test_streaming_read_no_numeric_params_unchanged(self):
        partial = '{"file_path":"a.py"}'
        result = streaming_transform_partial(partial, "Read", provider="gemini")
        assert result == partial

    # --- NotebookEdit ---
    def test_streaming_notebookedit_cell_number(self):
        partial = '{"notebook_path":"nb.ipynb","cell_number":"5"}'
        result = streaming_transform_partial(partial, "NotebookEdit", provider="gemini")
        assert '"cell_number":5' in result
        assert '"cell_number":"5"' not in result

    # --- Non-affected tools ---
    def test_streaming_non_affected_tool_unmodified(self):
        partial = '{"pattern":"*.py","timeout":"10"}'
        result = streaming_transform_partial(partial, "Grep", provider="gemini")
        # Grep has no numeric coercion — should pass through unchanged
        assert result == partial
