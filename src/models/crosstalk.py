"""
Pydantic models for crosstalk API requests and responses.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class CrosstalkSetupRequest(BaseModel):
    """Request to setup a new crosstalk session."""
    models: List[str] = Field(
        description="List of models to use (e.g., ['big', 'small', 'middle'])",
        example=["big", "small"]
    )
    system_prompts: Optional[Dict[str, str]] = Field(
        default=None,
        description="System prompts for each model (key=model, value=prompt or file path)",
        example={"big": "path:prompts/alice.txt", "small": "path:prompts/bob.txt"}
    )
    paradigm: str = Field(
        default="relay",
        description="Communication paradigm (memory|report|relay|debate)",
        example="debate"
    )
    iterations: int = Field(
        default=20,
        description="Number of conversation exchanges",
        ge=1,
        le=100,
        example=20
    )
    topic: str = Field(
        default="",
        description="Initial topic or message",
        example="hery whats up"
    )


class CrosstalkSetupResponse(BaseModel):
    """Response from crosstalk setup."""
    session_id: str = Field(
        description="Unique session ID for the crosstalk",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    status: str = Field(
        description="Setup status",
        example="configured"
    )
    models: List[str] = Field(
        description="Models configured for this session",
        example=["big", "small"]
    )
    paradigm: str = Field(
        description="Communication paradigm",
        example="debate"
    )
    iterations: int = Field(
        description="Number of iterations",
        example=20
    )


class CrosstalkRunResponse(BaseModel):
    """Response from crosstalk execution."""
    session_id: str = Field(
        description="Session ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    status: str = Field(
        description="Execution status",
        example="completed"
    )
    conversation: List[Dict[str, Any]] = Field(
        description="Complete conversation history",
        example=[
            {
                "speaker": "big",
                "listener": "small",
                "content": "Hello!",
                "iteration": 0,
                "timestamp": 1234567890.0,
                "confidence": 0.8,
                "message_type": "regular"
            }
        ]
    )
    duration_seconds: float = Field(
        description="Total execution time",
        example=45.2
    )


class CrosstalkStatusResponse(BaseModel):
    """Response for crosstalk status request."""
    session_id: str = Field(
        description="Session ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    status: str = Field(
        description="Current status (configured|running|completed|error)",
        example="running"
    )
    models: List[str] = Field(
        description="Models in this session",
        example=["big", "small"]
    )
    paradigm: str = Field(
        description="Communication paradigm",
        example="relay"
    )
    iterations: int = Field(
        description="Total iterations",
        example=20
    )
    current_iteration: int = Field(
        description="Current iteration",
        example=5
    )
    message_count: int = Field(
        description="Number of messages so far",
        example=10
    )
    created_at: float = Field(
        description="Session creation timestamp",
        example=1234567890.0
    )


class CrosstalkListResponse(BaseModel):
    """Response listing all crosstalk sessions."""
    sessions: List[Dict[str, Any]] = Field(
        description="List of active sessions",
        example=[
            {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "models": ["big", "small"],
                "paradigm": "debate",
                "iterations": 20,
                "message_count": 40,
                "created_at": 1234567890.0
            }
        ]
    )
    total: int = Field(
        description="Total number of sessions",
        example=1
    )


class CrosstalkDeleteResponse(BaseModel):
    """Response for crosstalk deletion."""
    success: bool = Field(
        description="Whether deletion was successful",
        example=True
    )
    message: str = Field(
        description="Deletion status message",
        example="Session deleted successfully"
    )


class CrosstalkError(BaseModel):
    """Error response for crosstalk endpoints."""
    error: str = Field(
        description="Error type",
        example="SessionNotFound"
    )
    message: str = Field(
        description="Error message",
        example="Session 550e8400-e29b-41d4-a716-446655440000 not found"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
        example={"session_id": "550e8400-e29b-41d4-a716-446655440000"}
    )