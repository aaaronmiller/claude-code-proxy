from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import uuid
import time
import os
from typing import Optional

from src.core.config import config
from src.core.logging import logger
from src.core.client import OpenAIClient
from src.models.claude import ClaudeMessagesRequest, ClaudeTokenCountRequest
from src.services.conversion.request_converter import convert_claude_to_openai
from src.services.conversion.response_converter import (
    convert_openai_to_claude_response,
    convert_openai_streaming_to_claude_with_cancellation,
    convert_openai_streaming_to_claude
)
from src.core.model_manager import model_manager
from src.services.logging.request_logger import request_logger, RequestLogger
from src.services.logging.compact_logger import compact_logger
from src.services.usage.usage_tracker import usage_tracker
from src.services.usage.model_limits import check_model_limits
from src.services.models.model_filter import filter_models
from src.services.prompts.prompt_injection_middleware import inject_system_prompts
from src.services.usage.model_limits import get_model_limits
from src.conversation.crosstalk import crosstalk_orchestrator
from src.dashboard.dashboard_hooks import dashboard_hooks
from src.models.crosstalk import (
    CrosstalkSetupRequest,
    CrosstalkSetupResponse,
    CrosstalkRunResponse,
    CrosstalkStatusResponse,
    CrosstalkListResponse,
    CrosstalkDeleteResponse,
    CrosstalkError,
)

router = APIRouter()

# Choose logger based on environment variable
USE_COMPACT_LOGGER = os.getenv("USE_COMPACT_LOGGER", "false").lower() == "true"
active_logger = compact_logger if USE_COMPACT_LOGGER else request_logger

# Get custom headers from config
custom_headers = config.get_custom_headers()

openai_client = OpenAIClient(
    config.openai_api_key,
    config.openai_base_url,
    config.request_timeout,
    api_version=config.azure_api_version,
    custom_headers=custom_headers,
)

# Configure per-model clients for hybrid deployments
openai_client.configure_per_model_clients(config)

async def validate_and_extract_api_key(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    openai_api_key: Optional[str] = Header(None, alias="openai-api-key")
) -> Optional[str]:
    """
    Validate and extract API keys based on operating mode.

    Returns:
        OpenAI API key to use for the request (None in proxy mode)

    Raises:
        HTTPException: If validation fails
    """
    client_api_key = None
    openai_key = None

    # Extract Anthropic API key from headers (for Claude client validation)
    if x_api_key:
        client_api_key = x_api_key
        logger.debug(f"API key from x-api-key header: {client_api_key[:10]}...")
    elif authorization and authorization.startswith("Bearer "):
        client_api_key = authorization.replace("Bearer ", "")
        logger.debug(f"API key from Authorization header: {client_api_key[:10]}...")

    # Extract OpenAI API key from headers (for passthrough mode)
    if openai_api_key:
        openai_key = openai_api_key
        logger.debug(f"OpenAI API key from header: {openai_key[:10]}...")

    # Passthrough mode: Require OpenAI API key from user
    if config.passthrough_mode:
        if not openai_key:
            raise HTTPException(
                status_code=401,
                detail="Passthrough mode: Please provide your OpenAI API key via 'openai-api-key' header"
            )

        # Validate OpenAI API key format
        if not config.validate_api_key(openai_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenAI API key format. Key must start with 'sk-' and be at least 20 characters"
            )

        logger.debug("Passthrough mode: OpenAI API key validated")
        return openai_key

    # Proxy mode: Validate Anthropic client key if configured
    if config.anthropic_api_key:
        if not client_api_key or not config.validate_client_api_key(client_api_key):
            logger.warning(f"Invalid API key provided by client. Expected: {config.anthropic_api_key}, Got: {client_api_key[:10] if client_api_key else 'None'}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please provide a valid Anthropic API key."
            )
        logger.debug("Proxy mode: Anthropic API key validation passed")

    return None  # Proxy mode: use server-configured API key

@router.post("/v1/messages")
async def create_message(
    request: ClaudeMessagesRequest,
    http_request: Request,
    openai_api_key: Optional[str] = Depends(validate_and_extract_api_key)
):
    request_start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        logger.debug(
            f"Processing Claude request: model={request.model}, stream={request.stream}"
        )
        logger.debug(f"Request ID: {request_id}")

        # Convert Claude request to OpenAI format and extract reasoning config
        openai_request = convert_claude_to_openai(request, model_manager)
        
        # Parse model to get routing info and reasoning config
        routed_model, reasoning_config = model_manager.parse_and_map_model(request.model)
        
        # Determine endpoint
        client = openai_client.get_client_for_model(routed_model, config)
        endpoint = config.openai_base_url
        if client == openai_client.big_client:
            endpoint = config.big_endpoint
        elif client == openai_client.middle_client:
            endpoint = config.middle_endpoint
        elif client == openai_client.small_client:
            endpoint = config.small_endpoint

        # Log API configuration for debugging (helps diagnose 401 errors)
        logger.debug(f"Request {request_id}: Routing to endpoint: {endpoint}")
        logger.debug(f"Request {request_id}: Using model: {routed_model}")
        if openai_api_key:
            logger.debug(f"Request {request_id}: Using passthrough mode with user-provided API key")
        else:
            api_key_preview = config.openai_api_key[:15] if config.openai_api_key else "None"
            logger.debug(f"Request {request_id}: Using proxy mode with server API key: {api_key_preview}...")

        # Extract request metadata for comprehensive logging
        message_count = len(request.messages)
        has_system = bool(request.system)
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Extract input text for token counting and workspace detection
        input_text = ""
        workspace_name = None

        def extract_workspace_name(text: str) -> Optional[str]:
            """Extract workspace/project name from system prompt text."""
            try:
                import re
                import os

                # Try multiple patterns in order of preference
                patterns = [
                    # Claude Code pattern: "Working directory: /path/to/project"
                    r'Working directory:\s+([^\n]+)',
                    # Git path pattern: /something/git/project-name
                    r'/git/([^/\s]+)',
                    # Generic path pattern: extract last folder name from absolute paths
                    r'/([a-zA-Z0-9_-]+)(?:/[a-zA-Z0-9_.-]+)*\s',
                    # Workspace keyword pattern
                    r'workspace.*?:?\s+([a-zA-Z0-9_-]+)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        # If it's a full path, extract just the last folder name
                        if '/' in candidate:
                            candidate = os.path.basename(candidate.rstrip('/'))
                        # Skip common parent folders
                        skip_names = ['users', 'home', 'user', 'documents', 'projects', 'git', 'code', 'my_projects', '0my_projects']
                        if candidate.lower() not in skip_names and len(candidate) > 0:
                            # Shorten if too long
                            if len(candidate) > 20:
                                return candidate[:17] + "..."
                            return candidate
                return None
            except Exception as e:
                # If workspace extraction fails, just return None - don't break the request
                logger.debug(f"Workspace name extraction failed: {e}")
                return None

        if request.system:
            if isinstance(request.system, str):
                input_text += request.system
                workspace_name = extract_workspace_name(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, "text"):
                        input_text += block.text
                        if not workspace_name and block.text:
                            workspace_name = extract_workspace_name(block.text)
        
        for msg in request.messages:
            if isinstance(msg.content, str):
                input_text += msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "text") and block.text:
                        input_text += block.text
        
        # Get model limits and token counts for logging
        # Get model limits and token counts for logging
        from src.services.usage.model_limits import get_model_limits
        context_limit, output_limit = get_model_limits(routed_model)
        
        # Estimate input tokens
        input_tokens = 0
        if input_text:
            # Rough estimate: ~4 characters per token
            input_tokens = max(1, len(input_text) // 4)

        # Detect images and tools
        has_images = False
        has_tools = bool(request.tools)
        for msg in request.messages:
            if isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "type") and block.type == "image":
                        has_images = True
                        break

        # Log comprehensive request start
        active_logger.log_request_start(
            request_id=request_id,
            original_model=request.model,
            routed_model=routed_model,
            endpoint=endpoint,
            reasoning_config=reasoning_config,
            stream=request.stream,
            input_text=input_text,
            context_limit=context_limit,
            output_limit=output_limit,
            input_tokens=input_tokens,
            message_count=message_count,
            has_system=has_system,
            has_tools=has_tools,
            has_images=has_images,
            client_info=client_ip,
            workspace_name=workspace_name
        )

        # Dashboard hook: request start
        dashboard_hooks.on_request_start(request_id, {
            'model': routed_model,
            'stream': request.stream,
            'has_tools': has_tools,
            'has_images': has_images,
            'input_tokens': input_tokens
        })

        # Check if client disconnected before processing
        if await http_request.is_disconnected():
            logger.warning(f"Client disconnected before processing request_id: {request_id}")
            raise HTTPException(status_code=499, detail="Client disconnected")

        if request.stream:
            # Streaming response - wrap in error handling
            logger.debug(f"Starting streaming response for request_id: {request_id}")
            try:
                openai_stream = openai_client.create_chat_completion_stream(
                    openai_request, request_id, config, api_key=openai_api_key
                )
                logger.debug(f"OpenAI stream created for request_id: {request_id}")
                return StreamingResponse(
                    convert_openai_streaming_to_claude_with_cancellation(
                        openai_stream,
                        request,
                        logger,
                        http_request,
                        openai_client,
                        request_id,
                        config,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                    },
                )
            except HTTPException as e:
                # Convert to proper error response for streaming
                logger.error(f"Streaming HTTPException for request_id {request_id}: status={e.status_code}, detail={e.detail}")
                import traceback

                logger.error(f"Streaming traceback: {traceback.format_exc()}")
                error_message = openai_client.classify_openai_error(e.detail)
                error_response = {
                    "type": "error",
                    "error": {"type": "api_error", "message": error_message},
                }
                return JSONResponse(status_code=e.status_code, content=error_response)
            except Exception as e:
                logger.error(f"Unexpected streaming error for request_id {request_id}: {e}")
                import traceback
                logger.error(f"Streaming traceback: {traceback.format_exc()}")
                error_message = openai_client.classify_openai_error(str(e))
                error_response = {
                    "type": "error",
                    "error": {"type": "api_error", "message": error_message},
                }
                return JSONResponse(status_code=500, content=error_response)
        else:
            # Non-streaming response
            logger.debug(f"Starting non-streaming response for request_id: {request_id}")
            
            # Seamless Key Rotation / Retry Loop
            # If we get a 401, we wait for the user to fix the key via the wizard
            from src.utils.key_reloader import key_reloader
            import asyncio
            
            max_retries = 150  # Wait up to 300 seconds (5 minutes)
            retry_count = 0
            
            while True:
                try:
                    openai_response = await openai_client.create_chat_completion(
                        openai_request, request_id, config, api_key=openai_api_key
                    )
                    break # Success!
                    
                except HTTPException as e:
                    if e.status_code == 401 and not openai_api_key: # Only retry for server-side keys (proxy mode)
                        if retry_count >= max_retries:
                            logger.error(f"Authentication failed. Timed out waiting for key update.")
                            raise e
                        
                        if retry_count == 0:
                            logger.warning(f"Authentication failed (401). Waiting for key update in profile...")
                            logger.warning(f"Run 'cproxy-init' or the wizard to fix your key.")
                        
                        # Wait and check for updates
                        await asyncio.sleep(2)
                        retry_count += 1
                        
                        if key_reloader.check_for_updates():
                            logger.info("Key update detected! Retrying request...")
                            # Re-configure client with new key
                            openai_client.api_key = config.openai_api_key
                            continue
                        
                        # Log progress every 10 seconds
                        if retry_count % 5 == 0:
                            logger.info(f"Still waiting for key update... ({retry_count * 2}s elapsed)")
                    else:
                        raise e # Re-raise other errors immediately

            logger.debug(f"OpenAI response received for request_id: {request_id}")
            
            # Log comprehensive completion with all metadata
            duration_ms = (time.time() - request_start_time) * 1000
            usage = openai_response.get("usage", {})

            # Detect JSON for TOON analysis
            has_json_content = False
            json_size_bytes = 0
            if input_text:
                has_json, json_bytes, _ = json_detector.detect_json_in_text(input_text)
                has_json_content = has_json
                json_size_bytes = json_bytes

            # Extract provider from endpoint
            provider = "unknown"
            if "openrouter" in endpoint.lower():
                provider = "openrouter"
            elif "openai" in endpoint.lower():
                provider = "openai"
            elif "anthropic" in endpoint.lower():
                provider = "anthropic"
            elif "azure" in endpoint.lower():
                provider = "azure"

            # Calculate cost
            estimated_cost = calculate_cost(usage, routed_model)

            # Log to active logger
            active_logger.log_request_complete(
                request_id=request_id,
                usage=usage,
                duration_ms=duration_ms,
                status="OK",
                model_name=routed_model,
                stream=request.stream,
                has_reasoning=bool(reasoning_config)
            )

            # Track usage if enabled
            if usage_tracker.enabled:
                usage_tracker.log_request(
                    request_id=request_id,
                    original_model=request.model,
                    routed_model=routed_model,
                    provider=provider,
                    endpoint=endpoint,
                    input_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                    output_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
                    thinking_tokens=usage.get("thinking_tokens", 0),
                    duration_ms=duration_ms,
                    estimated_cost=estimated_cost,
                    stream=request.stream,
                    message_count=message_count,
                    has_system=has_system,
                    has_tools=has_tools,
                    has_images=has_images,
                    status="success",
                    session_id=request_id[:8],
                    client_ip=client_ip,
                    has_json_content=has_json_content,
                    json_size_bytes=json_size_bytes
                )

            claude_response = convert_openai_to_claude_response(
                openai_response, request
            )
            logger.debug(f"Claude response created for request_id: {request_id}")

            # Dashboard hook: request complete
            dashboard_hooks.on_request_complete(request_id, 'completed', {
                'model': routed_model,
                'duration_ms': int(duration_ms),
                'input_tokens': usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                'output_tokens': usage.get("output_tokens", usage.get("completion_tokens", 0)),
                'thinking_tokens': usage.get("thinking_tokens", 0),
                'tokens': usage.get("total_tokens", 0),
                'cost': estimated_cost,
                'tokens_per_sec': int(usage.get("total_tokens", 0) / (duration_ms / 1000)) if duration_ms > 0 else 0,
                'has_tools': has_tools,
                'has_images': has_images,
                'context_tokens': input_tokens,
                'context_limit': context_limit
            })

            return claude_response
    except HTTPException as e:
        duration_ms = (time.time() - request_start_time) * 1000

        # Log error
        active_logger.log_request_error(
            request_id=request_id,
            error=e.detail,
            duration_ms=duration_ms
        )

        # Track error if enabled
        if usage_tracker.enabled:
            usage_tracker.log_request(
                request_id=request_id,
                original_model=request.model,
                routed_model=routed_model,
                provider="unknown",
                endpoint=endpoint,
                status="error",
                error_message=str(e.detail),
                duration_ms=duration_ms,
                session_id=request_id[:8],
                client_ip=client_ip
            )

        # Enhanced error logging for 401 errors
        if e.status_code == 401:
            logger.error(f"Authentication failed for request {request_id}")
            logger.error(f"Endpoint: {endpoint if 'endpoint' in locals() else 'unknown'}")
            logger.error(f"Model: {routed_model if 'routed_model' in locals() else request.model}")
            if config.passthrough_mode:
                logger.error("Running in PASSTHROUGH mode - check client-provided API key")
            else:
                logger.error("Running in PROXY mode - check server OPENAI_API_KEY configuration")
                logger.error("Note: OPENAI_API_KEY is used for ANY provider (OpenRouter, OpenAI, Azure, etc.)")
                if config.openai_api_key:
                    logger.error(f"Server API key prefix: {config.openai_api_key[:15]}...")
                else:
                    logger.error("Server API key is NOT SET - this will cause 401 errors!")
            logger.error(f"See docs/TROUBLESHOOTING_401.md for detailed troubleshooting steps")

        # Dashboard hook: request error
        error_type = "Unknown"
        if e.status_code == 401:
            error_type = "Invalid Key"
        elif e.status_code == 429:
            error_type = "Rate Limit"
        elif e.status_code == 404:
            error_type = "Model Not Found"

        dashboard_hooks.on_request_complete(request_id, 'error', {
            'model': routed_model if 'routed_model' in locals() else request.model,
            'duration_ms': int(duration_ms),
            'error': str(e.detail),
            'error_type': error_type
        })

        logger.error(f"HTTPException in create_message for request_id {request_id}: status={e.status_code}, detail={e.detail}")
        raise
    except Exception as e:
        import traceback

        duration_ms = (time.time() - request_start_time) * 1000
        error_message = openai_client.classify_openai_error(str(e))

        # Log error
        active_logger.log_request_error(
            request_id=request_id,
            error=error_message,
            duration_ms=duration_ms
        )

        # Track error if enabled
        if usage_tracker.enabled:
            usage_tracker.log_request(
                request_id=request_id,
                original_model=request.model if hasattr(request, 'model') else "unknown",
                routed_model="unknown",
                provider="unknown",
                endpoint="unknown",
                status="error",
                error_message=error_message,
                duration_ms=duration_ms,
                session_id=request_id[:8],
                client_ip="unknown"
            )

        # Dashboard hook: request error
        dashboard_hooks.on_request_complete(request_id, 'error', {
            'model': routed_model if 'routed_model' in locals() else (request.model if hasattr(request, 'model') else "unknown"),
            'duration_ms': int(duration_ms),
            'error': error_message,
            'error_type': "Unknown"
        })

        logger.error(f"Unexpected error processing request {request_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/v1/messages/count_tokens")
async def count_tokens(
    request: ClaudeTokenCountRequest,
    openai_api_key: Optional[str] = Depends(validate_and_extract_api_key)
):
    try:
        # For token counting, we'll use a simple estimation
        # In a real implementation, you might want to use tiktoken or similar

        total_chars = 0

        # Count system message characters
        if request.system:
            if isinstance(request.system, str):
                total_chars += len(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, "text"):
                        total_chars += len(block.text)

        # Count message characters
        for msg in request.messages:
            if msg.content is None:
                continue
            elif isinstance(msg.content, str):
                total_chars += len(msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "text") and block.text is not None:
                        total_chars += len(block.text)

        # Rough estimation: 4 characters per token
        estimated_tokens = max(1, total_chars // 4)

        return {"input_tokens": estimated_tokens}

    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_api_configured": bool(config.openai_api_key),
        "api_key_valid": config.validate_api_key(),
        "client_api_key_validation": bool(config.anthropic_api_key),
    }


@router.get("/test-connection")
async def test_connection():
    """Test API connectivity to OpenAI"""
    try:
        # Simple test request to verify API connectivity
        # Check if the test model is a newer OpenAI model
        is_newer_model = model_manager.is_newer_openai_model(config.small_model)

        test_request = {
            "model": config.small_model,
            "messages": [{"role": "user", "content": "Hello"}],
        }

        # Newer OpenAI models (o1, o3, o4, gpt-5) require max_completion_tokens and temperature=1
        if is_newer_model:
            test_request["max_completion_tokens"] = 200
            test_request["temperature"] = 1
        else:
            test_request["max_tokens"] = 5

        test_response = await openai_client.create_chat_completion(
            test_request,
            config=config
        )

        return {
            "status": "success",
            "message": "Successfully connected to OpenAI API",
            "model_used": config.small_model,
            "timestamp": datetime.now().isoformat(),
            "response_id": test_response.get("id", "unknown"),
        }

    except Exception as e:
        logger.error(f"API connectivity test failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "failed",
                "error_type": "API Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "suggestions": [
                    "Check your OPENAI_API_KEY is valid",
                    "Verify your API key has the necessary permissions",
                    "Check if you have reached rate limits",
                ],
            },
        )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Claude-to-OpenAI API Proxy v1.0.0",
        "status": "running",
        "config": {
            "openai_base_url": config.openai_base_url,
            "max_tokens_limit": config.max_tokens_limit,
            "api_key_configured": bool(config.openai_api_key),
            "client_api_key_validation": bool(config.anthropic_api_key),
            "big_model": config.big_model,
            "small_model": config.small_model,
        },
        "endpoints": {
            "messages": "/v1/messages",
            "count_tokens": "/v1/messages/count_tokens",
            "health": "/health",
            "test_connection": "/test-connection",
            "crosstalk": {
                "setup": "/v1/crosstalk/setup",
                "run": "/v1/crosstalk/{session_id}/run",
                "status": "/v1/crosstalk/{session_id}/status",
                "list": "/v1/crosstalk/list",
                "delete": "/v1/crosstalk/{session_id}/delete",
            },
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CROSSTALK ENDPOINTS - Model-to-Model Conversations
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/v1/crosstalk/setup")
async def setup_crosstalk(
    request: CrosstalkSetupRequest,
) -> CrosstalkSetupResponse:
    """
    Setup a new crosstalk session.

    This endpoint configures a model-to-model conversation using Exchange-of-Thought
    (EoT) paradigms: Memory, Report, Relay, or Debate.
    """
    try:
        session_id = await crosstalk_orchestrator.setup_crosstalk(
            models=request.models,
            system_prompts=request.system_prompts,
            paradigm=request.paradigm,
            iterations=request.iterations,
            topic=request.topic
        )

        return CrosstalkSetupResponse(
            session_id=session_id,
            status="configured",
            models=request.models,
            paradigm=request.paradigm,
            iterations=request.iterations
        )

    except Exception as e:
        logger.error(f"Crosstalk setup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/v1/crosstalk/{session_id}/run")
async def run_crosstalk(
    session_id: str,
) -> CrosstalkRunResponse:
    """
    Execute a configured crosstalk session.

    Runs the model-to-model conversation and returns the complete transcript.
    """
    try:
        start_time = time.time()
        conversation = await crosstalk_orchestrator.execute_crosstalk(session_id)
        duration = time.time() - start_time

        return CrosstalkRunResponse(
            session_id=session_id,
            status="completed",
            conversation=conversation,
            duration_seconds=duration
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Crosstalk execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/crosstalk/{session_id}/status")
async def crosstalk_status(
    session_id: str,
) -> CrosstalkStatusResponse:
    """
    Get the status of a crosstalk session.
    """
    status = crosstalk_orchestrator.get_session_status(session_id)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return CrosstalkStatusResponse(**status)


@router.get("/v1/crosstalk/list")
async def list_crosstalk_sessions() -> CrosstalkListResponse:
    """
    List all active crosstalk sessions.
    """
    sessions = []
    for session_id in crosstalk_orchestrator.active_sessions:
        status = crosstalk_orchestrator.get_session_status(session_id)
        sessions.append(status)

    return CrosstalkListResponse(
        sessions=sessions,
        total=len(sessions)
    )


@router.delete("/v1/crosstalk/{session_id}/delete")
async def delete_crosstalk_session(
    session_id: str,
) -> CrosstalkDeleteResponse:
    """
    Delete a completed or errored crosstalk session.
    """
    success = crosstalk_orchestrator.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return CrosstalkDeleteResponse(
        success=True,
        message="Session deleted successfully"
    )
