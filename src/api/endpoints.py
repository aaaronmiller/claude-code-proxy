from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import uuid
import time
from typing import Optional

from src.core.config import config
from src.core.logging import logger
from src.core.client import OpenAIClient
from src.models.claude import ClaudeMessagesRequest, ClaudeTokenCountRequest
from src.conversion.request_converter import convert_claude_to_openai
from src.conversion.response_converter import (
    convert_openai_to_claude_response,
    convert_openai_streaming_to_claude_with_cancellation,
)
from src.core.model_manager import model_manager
from src.utils.request_logger import request_logger
from src.utils.model_limits import get_model_limits
from src.conversation.crosstalk import crosstalk_orchestrator
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

openai_client = OpenAIClient(
    config.openai_api_key,
    config.openai_base_url,
    config.request_timeout,
    api_version=config.azure_api_version,
)

# Configure per-model clients for hybrid deployments
openai_client.configure_per_model_clients(config)

async def validate_api_key(x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None)):
    """Validate the client's API key from either x-api-key header or Authorization header."""
    client_api_key = None

    # Extract API key from headers
    if x_api_key:
        client_api_key = x_api_key
        logger.debug(f"API key from x-api-key header: {client_api_key[:10]}...")
    elif authorization and authorization.startswith("Bearer "):
        client_api_key = authorization.replace("Bearer ", "")
        logger.debug(f"API key from Authorization header: {client_api_key[:10]}...")

    # Skip validation if ANTHROPIC_API_KEY is not set in the environment
    if not config.anthropic_api_key:
        logger.debug("ANTHROPIC_API_KEY not set, skipping client validation")
        return

    logger.debug(f"Expected ANTHROPIC_API_KEY: {config.anthropic_api_key}")

    # Validate the client API key
    if not client_api_key or not config.validate_client_api_key(client_api_key):
        logger.warning(f"Invalid API key provided by client. Expected: {config.anthropic_api_key}, Got: {client_api_key[:10] if client_api_key else 'None'}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please provide a valid Anthropic API key."
        )

    logger.debug("API key validation passed")

@router.post("/v1/messages")
async def create_message(request: ClaudeMessagesRequest, http_request: Request, _: None = Depends(validate_api_key)):
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
        
        # Extract input text for token counting
        input_text = ""
        if request.system:
            if isinstance(request.system, str):
                input_text += request.system
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, "text"):
                        input_text += block.text
        
        for msg in request.messages:
            if isinstance(msg.content, str):
                input_text += msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "text") and block.text:
                        input_text += block.text
        
        # Log request start with compact format
        request_logger.log_request_start(
            request_id=request_id,
            original_model=request.model,
            routed_model=routed_model,
            endpoint=endpoint,
            reasoning_config=reasoning_config,
            stream=request.stream,
            input_text=input_text
        )
        
        # Show context window usage visualization
        context_limit, output_limit = get_model_limits(routed_model)
        if context_limit > 0:
            # Estimate input tokens from text
            input_tokens = len(input_text) // 4  # Rough estimate
            request_logger.log_context_window_usage(
                request_id=request_id,
                input_tokens=input_tokens,
                context_limit=context_limit,
                model_name=routed_model
            )

        # Check if client disconnected before processing
        if await http_request.is_disconnected():
            logger.warning(f"Client disconnected before processing request_id: {request_id}")
            raise HTTPException(status_code=499, detail="Client disconnected")

        if request.stream:
            # Streaming response - wrap in error handling
            logger.debug(f"Starting streaming response for request_id: {request_id}")
            try:
                openai_stream = openai_client.create_chat_completion_stream(
                    openai_request, request_id, config
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
            openai_response = await openai_client.create_chat_completion(
                openai_request, request_id, config
            )
            logger.debug(f"OpenAI response received for request_id: {request_id}")
            
            # Log completion with usage stats
            duration_ms = (time.time() - request_start_time) * 1000
            usage = openai_response.get("usage", {})
            
            request_logger.log_request_complete(
                request_id=request_id,
                usage=usage,
                duration_ms=duration_ms,
                status="OK"
            )
            
            # Show output token usage visualization
            context_limit, output_limit = get_model_limits(routed_model)
            if output_limit > 0 and usage:
                output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))
                thinking_tokens = 0
                
                # Extract thinking tokens
                if "thinking_tokens" in usage:
                    thinking_tokens = usage["thinking_tokens"]
                elif "reasoning_tokens" in usage:
                    thinking_tokens = usage["reasoning_tokens"]
                elif "completion_tokens_details" in usage:
                    details = usage["completion_tokens_details"]
                    if isinstance(details, dict):
                        thinking_tokens = details.get("reasoning_tokens", 0)
                
                request_logger.log_output_token_usage(
                    request_id=request_id,
                    output_tokens=output_tokens,
                    output_limit=output_limit,
                    thinking_tokens=thinking_tokens
                )
            
            claude_response = convert_openai_to_claude_response(
                openai_response, request
            )
            logger.debug(f"Claude response created for request_id: {request_id}")
            return claude_response
    except HTTPException as e:
        duration_ms = (time.time() - request_start_time) * 1000
        request_logger.log_request_error(
            request_id=request_id,
            error=e.detail,
            duration_ms=duration_ms
        )
        logger.error(f"HTTPException in create_message for request_id {request_id}: status={e.status_code}, detail={e.detail}")
        raise
    except Exception as e:
        import traceback
        
        duration_ms = (time.time() - request_start_time) * 1000
        error_message = openai_client.classify_openai_error(str(e))
        request_logger.log_request_error(
            request_id=request_id,
            error=error_message,
            duration_ms=duration_ms
        )

        logger.error(f"Unexpected error processing request {request_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/v1/messages/count_tokens")
async def count_tokens(request: ClaudeTokenCountRequest, _: None = Depends(validate_api_key)):
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
        test_response = await openai_client.create_chat_completion(
            {
                "model": config.small_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
            },
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
