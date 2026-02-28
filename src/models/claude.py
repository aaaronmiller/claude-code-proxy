from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal


class ClaudeContentBlockText(BaseModel):
    type: Literal["text"]
    text: str


class ClaudeContentBlockImage(BaseModel):
    type: Literal["image"]
    source: Dict[str, Any]


class ClaudeContentBlockToolUse(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: Dict[str, Any]


class ClaudeContentBlockToolResult(BaseModel):
    type: Literal["tool_result"]
    tool_use_id: str
    content: Union[str, List[Dict[str, Any]], Dict[str, Any]]


class ClaudeSystemContent(BaseModel):
    type: Literal["text"]
    text: str


class ClaudeContentBlockThinking(BaseModel):
    type: Literal["thinking"]
    thinking: str
    signature: Optional[str] = None


class ClaudeContentBlockRedactedThinking(BaseModel):
    type: Literal["redacted_thinking"]
    data: Optional[str] = None

    model_config = {"extra": "allow"}


class ClaudeMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[
        str,
        List[
            Union[
                ClaudeContentBlockText,
                ClaudeContentBlockImage,
                ClaudeContentBlockToolUse,
                ClaudeContentBlockToolResult,
                ClaudeContentBlockThinking,
                ClaudeContentBlockRedactedThinking,
            ]
        ],
    ]


class ClaudeTool(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]
    # Anthropic-specific fields preserved for injection/stripping
    input_examples: Optional[List[Dict[str, Any]]] = None
    allowed_callers: Optional[List[str]] = None


class ClaudeThinkingConfig(BaseModel):
    """
    Anthropic thinking tokens configuration.

    - type: "enabled" + budget_tokens for older models (Sonnet 4.5, Opus 4.5)
    - type: "adaptive" for Opus 4.6 (budget_tokens not required)

    budget_tokens range: 1024 to max_tokens.
    On Opus 4.6, type: "enabled" + budget_tokens is deprecated in favor of
    type: "adaptive" with the top-level effort parameter.
    """

    type: Literal["enabled", "adaptive"] = "enabled"
    budget_tokens: Optional[int] = Field(
        default=None,
        description="Thinking token budget (must be >= 1024 and < max_tokens)",
        ge=1024,
    )


class ClaudeMessagesRequest(BaseModel):
    model: str
    max_tokens: int
    messages: List[ClaudeMessage]
    system: Optional[Union[str, List[ClaudeSystemContent]]] = None
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tools: Optional[List[ClaudeTool]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    thinking: Optional[ClaudeThinkingConfig] = None
    effort: Optional[Literal["max", "high", "medium", "low"]] = None
    # Structured output support (GA Jan 2026+)
    output_format: Optional[Dict[str, Any]] = None   # Deprecated legacy field
    output_config: Optional[Dict[str, Any]] = None    # New GA format


class ClaudeTokenCountRequest(BaseModel):
    model: str
    messages: List[ClaudeMessage]
    system: Optional[Union[str, List[ClaudeSystemContent]]] = None
    tools: Optional[List[ClaudeTool]] = None
    thinking: Optional[ClaudeThinkingConfig] = None
    tool_choice: Optional[Dict[str, Any]] = None
