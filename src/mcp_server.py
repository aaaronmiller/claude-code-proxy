"""
MCP Server for Claude Code Proxy Crosstalk System
Provides tools for LLM integration with model-to-model conversations.
"""

import asyncio
import sys
import os
from typing import Any, Dict, List, Optional

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp.server import Server
from mcp.types import Tool, TextContent
from src.conversation.crosstalk import crosstalk_orchestrator, CrosstalkParadigm
from src.core.config import config


# Create the MCP server
app = Server("claude-code-proxy-crosstalk")


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List all available crosstalk tools.
    """
    return [
        Tool(
            name="crosstalk_setup",
            description="Setup a new model-to-model crosstalk conversation session",
            inputSchema={
                "type": "object",
                "properties": {
                    "models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of models to use (e.g., ['big', 'small'])",
                        "example": ["big", "small"]
                    },
                    "system_prompts": {
                        "type": "object",
                        "description": "System prompts for each model",
                        "example": {"big": "You are Alice", "small": "You are Bob"},
                        "additionalProperties": {"type": "string"}
                    },
                    "paradigm": {
                        "type": "string",
                        "enum": ["memory", "report", "relay", "debate"],
                        "description": "Communication paradigm",
                        "default": "relay",
                        "example": "debate"
                    },
                    "iterations": {
                        "type": "integer",
                        "description": "Number of conversation exchanges",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20,
                        "example": 20
                    },
                    "topic": {
                        "type": "string",
                        "description": "Initial topic or message",
                        "example": "hery whats up"
                    }
                },
                "required": ["models"]
            }
        ),
        Tool(
            name="crosstalk_run",
            description="Execute a configured crosstalk session and return the conversation",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from crosstalk_setup",
                        "example": "550e8400-e29b-41d4-a716-446655440000"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="crosstalk_status",
            description="Get the status of a crosstalk session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to check",
                        "example": "550e8400-e29b-41d4-a716-446655440000"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="crosstalk_list",
            description="List all active crosstalk sessions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="crosstalk_delete",
            description="Delete a completed or errored crosstalk session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to delete",
                        "example": "550e8400-e29b-41d4-a716-446655440000"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="load_system_prompt",
            description="Load a custom system prompt from file for a specific model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "enum": ["big", "middle", "small"],
                        "description": "Model to configure",
                        "example": "big"
                    },
                    "prompt_file": {
                        "type": "string",
                        "description": "Path to system prompt file",
                        "example": "prompts/alice.txt"
                    },
                    "enable": {
                        "type": "boolean",
                        "description": "Enable custom system prompt for this model",
                        "default": True,
                        "example": True
                    }
                },
                "required": ["model", "prompt_file"]
            }
        ),
        Tool(
            name="crosstalk_health",
            description="Check if the crosstalk system is healthy and ready",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Handle tool execution requests.
    """
    try:
        if name == "crosstalk_setup":
            return await _handle_crosstalk_setup(arguments)
        elif name == "crosstalk_run":
            return await _handle_crosstalk_run(arguments)
        elif name == "crosstalk_status":
            return await _handle_crosstalk_status(arguments)
        elif name == "crosstalk_list":
            return await _handle_crosstalk_list(arguments)
        elif name == "crosstalk_delete":
            return await _handle_crosstalk_delete(arguments)
        elif name == "load_system_prompt":
            return await _handle_load_system_prompt(arguments)
        elif name == "crosstalk_health":
            return await _handle_crosstalk_health(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]

    except Exception as e:
        import traceback
        error_msg = f"❌ Error executing {name}: {str(e)}\n\n{traceback.format_exc()}"
        return [TextContent(type="text", text=error_msg)]


async def _handle_crosstalk_setup(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle crosstalk setup."""
    models = arguments.get("models", [])
    if not models:
        return [TextContent(type="text", text="❌ Error: models parameter is required")]

    system_prompts = arguments.get("system_prompts")
    paradigm = arguments.get("paradigm", "relay")
    iterations = arguments.get("iterations", 20)
    topic = arguments.get("topic", "Hello, let's talk")

    # Validate paradigm
    if paradigm not in ["memory", "report", "relay", "debate"]:
        return [TextContent(type="text", text=f"❌ Invalid paradigm: {paradigm}")]

    session_id = await crosstalk_orchestrator.setup_crosstalk(
        models=models,
        system_prompts=system_prompts,
        paradigm=paradigm,
        iterations=iterations,
        topic=topic
    )

    response = f"""✅ Crosstalk session configured successfully!

Session ID: {session_id}
Models: {', '.join(models)}
Paradigm: {paradigm.upper()}
Iterations: {iterations}
Topic: {topic}

To execute this session, use the crosstalk_run tool with session_id: {session_id}"""

    return [TextContent(type="text", text=response)]


async def _handle_crosstalk_run(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle crosstalk execution."""
    session_id = arguments.get("session_id")
    if not session_id:
        return [TextContent(type="text", text="❌ Error: session_id parameter is required")]

    # Execute crosstalk
    import time
    start_time = time.time()

    conversation = await crosstalk_orchestrator.execute_crosstalk(session_id)
    duration = time.time() - start_time

    # Format conversation
    output = [TextContent(type="text", text="✅ Crosstalk completed!\n")]
    output.append(TextContent(
        type="text",
        text=f"Duration: {duration:.2f} seconds\nTotal messages: {len(conversation)}\n"
    ))

    output.append(TextContent(type="text", text="="*70))
    output.append(TextContent(type="text", text="CONVERSATION TRANSCRIPT"))
    output.append(TextContent(type="text", text="="*70))

    for i, msg in enumerate(conversation, 1):
        msg_text = f"\n[{i}] {msg['speaker'].upper()} → {msg['listener'].upper()} (iter {msg['iteration']})"
        if msg.get('confidence'):
            msg_text += f"\nConfidence: {msg['confidence']:.2f}"
        msg_text += f"\n{msg['content']}"

        output.append(TextContent(type="text", text=msg_text))

    return output


async def _handle_crosstalk_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle crosstalk status check."""
    session_id = arguments.get("session_id")
    if not session_id:
        return [TextContent(type="text", text="❌ Error: session_id parameter is required")]

    status = crosstalk_orchestrator.get_session_status(session_id)

    if "error" in status:
        return [TextContent(type="text", text=f"❌ {status['error']}")]

    response = f"""📊 Crosstalk Session Status

Session ID: {status['session_id']}
Status: {status['status'].upper()}
Models: {', '.join(status['models'])}
Paradigm: {status['paradigm'].upper()}
Iterations: {status['iterations']}
Current Iteration: {status['current_iteration']}
Messages: {status['message_count']}
Created: {status['created_at']}"""

    return [TextContent(type="text", text=response)]


async def _handle_crosstalk_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle listing all sessions."""
    sessions = []
    for sid in crosstalk_orchestrator.active_sessions:
        status = crosstalk_orchestrator.get_session_status(sid)
        sessions.append(status)

    if not sessions:
        return [TextContent(type="text", text="No active crosstalk sessions")]

    response = [TextContent(type="text", text=f"📋 Active Crosstalk Sessions ({len(sessions)})\n")]

    for status in sessions:
        response.append(TextContent(
            type="text",
            text=f"""
Session: {status['session_id'][:8]}...
Status: {status['status'].upper()}
Models: {', '.join(status['models'])}
Paradigm: {status['paradigm'].upper()}
Messages: {status['message_count']}
"""
        ))

    return response


async def _handle_crosstalk_delete(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle session deletion."""
    session_id = arguments.get("session_id")
    if not session_id:
        return [TextContent(type="text", text="❌ Error: session_id parameter is required")]

    success = crosstalk_orchestrator.delete_session(session_id)

    if success:
        return [TextContent(type="text", text=f"✅ Session {session_id} deleted successfully")]
    else:
        return [TextContent(type="text", text=f"❌ Session {session_id} not found")]


async def _handle_load_system_prompt(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle loading system prompt."""
    model = arguments.get("model")
    prompt_file = arguments.get("prompt_file")
    enable = arguments.get("enable", True)

    if not model or not prompt_file:
        return [TextContent(type="text", text="❌ Error: model and prompt_file are required")]

    if model not in ["big", "middle", "small"]:
        return [TextContent(type="text", text="❌ Error: model must be 'big', 'middle', or 'small'")]

    try:
        with open(prompt_file, 'r') as f:
            prompt = f.read().strip()

        # Set environment variables
        env_key = f"{model.upper()}_SYSTEM_PROMPT_FILE"
        os.environ[env_key] = prompt_file

        enable_key = f"ENABLE_CUSTOM_{model.upper()}_PROMPT"
        os.environ[enable_key] = "true" if enable else "false"

        return [TextContent(
            type="text",
            text=f"""✅ System prompt loaded for {model.upper()} model

File: {prompt_file}
Length: {len(prompt)} characters
Enabled: {enable}

The system will now use this custom system prompt for the {model.upper()} model.
Note: Changes will take effect when the proxy server restarts."""
        )]

    except FileNotFoundError:
        return [TextContent(type="text", text=f"❌ File not found: {prompt_file}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error loading prompt: {str(e)}")]


async def _handle_crosstalk_health(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle health check."""
    try:
        # Check if orchestrator is initialized
        orchestrator_status = "✅ Healthy" if crosstalk_orchestrator else "❌ Not initialized"

        # Check active sessions
        active_count = len(crosstalk_orchestrator.active_sessions)

        response = f"""🏥 Crosstalk System Health Check

Orchestrator: {orchestrator_status}
Active Sessions: {active_count}

Configuration:
  BIG Model: {config.big_model}
  MIDDLE Model: {config.middle_model}
  SMALL Model: {config.small_model}

Status: {'✅ All systems operational' if orchestrator_status == '✅ Healthy' else '❌ Issues detected'}"""

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Health check failed: {str(e)}"
        )]


if __name__ == "__main__":
    import sys

    # Check for stdio transport
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        import asyncio
        from mcp.server.stdio import stdio_server

        async def main():
            async with stdio_server() as (read_stream, write_stream):
                await app.run(
                    read_stream,
                    write_stream,
                    app.create_initialization_options()
                )

        asyncio.run(main())
    else:
        # Run withstdio server
        print("Starting MCP Server with stdio transport...")
        import asyncio
        from mcp.server.stdio import stdio_server

        async def main():
            async with stdio_server() as (read_stream, write_stream):
                await app.run(
                    read_stream,
                    write_stream,
                    app.create_initialization_options()
                )

        asyncio.run(main())
