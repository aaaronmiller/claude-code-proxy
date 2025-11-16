# Design Document: Advanced Reasoning Configuration

## Overview

This design implements fine-grained control over reasoning capabilities for OpenAI o-series models, Anthropic Claude models with thinking tokens, and Google Gemini models with thinking budgets. The implementation follows the suffix-based notation pattern from just-prompt, allowing users to specify reasoning parameters directly in model names (e.g., `claude-opus-4-20250514:4k`, `o4-mini:high`) or through environment variables.

The design integrates seamlessly with the existing proxy architecture, extending the Model Manager and Request Converter components to parse, validate, and apply reasoning parameters while maintaining backward compatibility.

## Architecture

### High-Level Flow

```
Client Request → Model Name Parser → Reasoning Parameter Extractor → Request Converter → Provider API
                      ↓                        ↓                            ↓
                Model Manager          Validation & Adjustment      API-Specific Formatting
```

### Component Responsibilities

1. **Model Name Parser**: Extracts base model name and reasoning suffix
2. **Reasoning Parameter Extractor**: Parses suffix into structured parameters
3. **Reasoning Validator**: Validates and adjusts parameters to provider-specific ranges
4. **Request Converter**: Applies reasoning parameters to API requests
5. **Model Manager**: Maintains model capability metadata and routing logic

## Components and Interfaces

### 1. Model Name Parser

**Location**: `src/utils/model_parser.py` (new file)

**Purpose**: Parse model names with reasoning suffixes into structured components

**Interface**:
```python
@dataclass
class ParsedModel:
    base_model: str
    reasoning_type: Optional[str]  # 'effort', 'thinking_tokens', 'thinking_budget'
    reasoning_value: Optional[Union[str, int]]
    original_model: str

def parse_model_name(model_name: str) -> ParsedModel:
    """
    Parse model name with optional reasoning suffix.
    
    Examples:
        'claude-opus-4-20250514:4k' → ParsedModel(
            base_model='claude-opus-4-20250514',
            reasoning_type='thinking_tokens',
            reasoning_value=4096,
            original_model='claude-opus-4-20250514:4k'
        )
        'o4-mini:high' → ParsedModel(
            base_model='o4-mini',
            reasoning_type='effort',
            reasoning_value='high',
            original_model='o4-mini:high'
        )
    """
```

**Implementation Details**:
- Use regex pattern `^(.+?)(?::([^:]+))?$` to split model name and suffix
- Detect reasoning type based on model family:
  - OpenAI o-series (o1, o3, o4-mini) → effort levels (low/medium/high)
  - Anthropic Claude 3.7/4.x → thinking tokens (1k-16k or exact numbers)
  - Gemini 2.5-flash → thinking budget (0-24k or exact numbers)
- Convert k-notation to exact token counts (1k → 1024, 4k → 4096, etc.)

### 2. Reasoning Configuration

**Location**: `src/models/reasoning.py` (new file)

**Purpose**: Define reasoning configuration data structures

**Interface**:
```python
@dataclass
class ReasoningConfig:
    """Base reasoning configuration"""
    enabled: bool = True
    
@dataclass
class OpenAIReasoningConfig(ReasoningConfig):
    """OpenAI o-series reasoning configuration"""
    effort: str  # 'low', 'medium', 'high'
    exclude: bool = False  # Whether to exclude reasoning tokens from response
    
@dataclass
class AnthropicThinkingConfig(ReasoningConfig):
    """Anthropic thinking tokens configuration"""
    budget: int  # 1024-16000
    type: str = "enabled"  # Always 'enabled' for Anthropic
    
@dataclass
class GeminiThinkingConfig(ReasoningConfig):
    """Gemini thinking budget configuration"""
    budget: int  # 0-24576
```

### 3. Reasoning Validator

**Location**: `src/utils/reasoning_validator.py` (new file)

**Purpose**: Validate and adjust reasoning parameters to provider-specific constraints

**Interface**:
```python
def validate_openai_reasoning(effort: str) -> str:
    """Validate OpenAI reasoning effort level"""
    
def validate_anthropic_thinking(budget: int) -> int:
    """Validate and adjust Anthropic thinking token budget to 1024-16000 range"""
    
def validate_gemini_thinking(budget: int) -> int:
    """Validate and adjust Gemini thinking budget to 0-24576 range"""
    
def is_reasoning_capable_model(model_name: str) -> tuple[bool, str]:
    """
    Check if model supports reasoning capabilities.
    Returns: (is_capable, reasoning_type)
    """
```

**Validation Rules**:

**OpenAI Reasoning Effort**:
- Valid values: 'low', 'medium', 'high'
- Invalid values raise ValueError with valid options

**Anthropic Thinking Tokens**:
- Minimum: 1024 (adjust if lower)
- Maximum: 16000 (adjust if higher)
- Supported models: claude-opus-4-20250514, claude-sonnet-4-20250514, claude-3-7-sonnet-20250219
- Log warning when adjusting values

**Gemini Thinking Budget**:
- Minimum: 0 (adjust if lower)
- Maximum: 24576 (adjust if higher)
- Supported model: gemini-2.5-flash-preview-04-17
- Log warning when adjusting values

### 4. Enhanced Model Manager

**Location**: `src/core/model_manager.py` (modify existing)

**New Methods**:
```python
def parse_and_map_model(self, claude_model: str) -> tuple[str, Optional[ReasoningConfig]]:
    """
    Parse model name with reasoning suffix and map to OpenAI model.
    Returns: (openai_model, reasoning_config)
    """
    
def get_model_capabilities(self, model_name: str) -> dict:
    """
    Get model capabilities including reasoning support.
    Returns: {
        'supports_reasoning': bool,
        'reasoning_type': str,  # 'effort', 'thinking_tokens', 'thinking_budget'
        'max_reasoning_tokens': int,
        'default_reasoning': Optional[ReasoningConfig]
    }
    """
```

**Model Capability Patterns**:
```python
REASONING_CAPABLE_MODELS = {
    'openai_o_series': {
        'patterns': [r'o1-', r'o3-', r'o4-mini', r'gpt-5'],
        'reasoning_type': 'effort',
        'default_effort': 'medium'
    },
    'anthropic_thinking': {
        'patterns': [
            r'claude-opus-4-',
            r'claude-sonnet-4-',
            r'claude-3-7-sonnet-'
        ],
        'reasoning_type': 'thinking_tokens',
        'min_tokens': 1024,
        'max_tokens': 16000
    },
    'gemini_thinking': {
        'patterns': [r'gemini-2\.5-flash-preview-04-17'],
        'reasoning_type': 'thinking_budget',
        'min_budget': 0,
        'max_budget': 24576
    }
}
```

### 5. Enhanced Request Converter

**Location**: `src/conversion/request_converter.py` (modify existing)

**Modified Function**:
```python
def convert_claude_to_openai(
    claude_request: ClaudeMessagesRequest, 
    model_manager: ModelManager
) -> Dict[str, Any]:
    """
    Convert Claude API request to OpenAI format with reasoning support.
    
    New logic:
    1. Parse model name for reasoning suffix
    2. Extract and validate reasoning parameters
    3. Apply reasoning config to request based on provider
    4. Merge with environment variable defaults
    """
```

**Reasoning Parameter Application**:

**For OpenAI o-series**:
```python
# Check if SDK supports Responses API
if hasattr(openai_client, 'responses') and hasattr(openai_client.responses, 'create'):
    # Use Responses API (preferred for o-series)
    openai_request['reasoning'] = {
        'effort': reasoning_config.effort
    }
else:
    # Fallback: embed in system message
    system_instruction = f"[Reasoning effort: {reasoning_config.effort}]"
    # Prepend to system message
```

**For Anthropic Claude**:
```python
# Anthropic uses 'thinking' parameter in request body
openai_request['thinking'] = {
    'type': 'enabled',
    'budget': reasoning_config.budget
}
```

**For Google Gemini**:
```python
# Gemini uses 'thinking_config' in generation_config
if 'generation_config' not in openai_request:
    openai_request['generation_config'] = {}
openai_request['generation_config']['thinking_config'] = {
    'budget': reasoning_config.budget
}
```

### 6. Enhanced Configuration

**Location**: `src/core/config.py` (modify existing)

**New Configuration Properties**:
```python
class Config:
    # Existing properties...
    
    # Reasoning configuration
    reasoning_effort: Optional[str]  # 'low', 'medium', 'high'
    reasoning_max_tokens: Optional[int]  # Default thinking token budget
    reasoning_exclude: bool  # Exclude reasoning tokens from response
    verbosity: Optional[str]  # Response verbosity level
    
    # Per-model reasoning overrides
    big_model_reasoning: Optional[str]  # Override for big model
    middle_model_reasoning: Optional[str]  # Override for middle model
    small_model_reasoning: Optional[str]  # Override for small model
```

**Environment Variable Mapping**:
```bash
# Global reasoning defaults
REASONING_EFFORT="high"  # low, medium, high
REASONING_MAX_TOKENS="8000"  # 1024-16000 for Anthropic
REASONING_EXCLUDE="false"  # true/false
VERBOSITY="high"  # Provider-specific

# Per-model overrides (optional)
BIG_MODEL_REASONING="high"
MIDDLE_MODEL_REASONING="medium"
SMALL_MODEL_REASONING="low"
```

## Data Models

### Extended Claude Request Model

**Location**: `src/models/claude.py` (modify existing)

```python
class ClaudeThinkingConfig(BaseModel):
    """Anthropic thinking configuration"""
    type: Literal["enabled"] = "enabled"
    budget: Optional[int] = None  # 1024-16000

class ClaudeMessagesRequest(BaseModel):
    # Existing fields...
    thinking: Optional[ClaudeThinkingConfig] = None
```

### OpenAI Request Extensions

**Location**: `src/models/openai.py` (create if needed)

```python
class OpenAIReasoningConfig(BaseModel):
    """OpenAI o-series reasoning configuration"""
    effort: Literal["low", "medium", "high"]
    
class OpenAIRequest(BaseModel):
    """OpenAI API request with reasoning support"""
    model: str
    messages: List[Dict[str, Any]]
    reasoning: Optional[OpenAIReasoningConfig] = None
    # Other standard OpenAI parameters...
```

## Error Handling

### Error Scenarios and Responses

1. **Invalid Reasoning Effort Level**
   ```python
   raise ValueError(
       f"Invalid reasoning effort '{effort}'. "
       f"Valid options: low, medium, high"
   )
   ```

2. **Invalid Thinking Token Budget**
   ```python
   logger.warning(
       f"Thinking token budget {budget} adjusted to valid range. "
       f"Original: {original_budget}, Adjusted: {adjusted_budget}, "
       f"Valid range: 1024-16000"
   )
   ```

3. **Reasoning Parameters on Incompatible Model**
   ```python
   logger.warning(
       f"Reasoning parameters specified for model '{model_name}' "
       f"which does not support reasoning. Parameters will be ignored. "
       f"Supported models: {', '.join(SUPPORTED_MODELS)}"
   )
   ```

4. **SDK Version Incompatibility**
   ```python
   logger.info(
       f"OpenAI SDK does not support Responses API. "
       f"Falling back to system message approach for reasoning effort."
   )
   ```

### Logging Strategy

- **DEBUG**: Parameter parsing and validation details
- **INFO**: Reasoning configuration applied, SDK fallbacks
- **WARNING**: Parameter adjustments, unsupported model warnings
- **ERROR**: Invalid configuration, API errors

## Testing Strategy

### Unit Tests

**Test File**: `tests/test_model_parser.py`
- Test model name parsing with various suffix formats
- Test k-notation conversion (1k → 1024, 4k → 4096, etc.)
- Test parsing without suffix (backward compatibility)
- Test invalid suffix formats

**Test File**: `tests/test_reasoning_validator.py`
- Test OpenAI effort validation (valid and invalid values)
- Test Anthropic thinking token range adjustment
- Test Gemini thinking budget range adjustment
- Test model capability detection for all providers

**Test File**: `tests/test_request_converter_reasoning.py`
- Test reasoning parameter application for OpenAI o-series
- Test thinking token application for Anthropic Claude
- Test thinking budget application for Gemini
- Test environment variable defaults
- Test suffix override of environment defaults
- Test reasoning parameters with streaming
- Test reasoning parameters with tool use

### Integration Tests

**Test File**: `tests/integration/test_reasoning_e2e.py`
- Test end-to-end request flow with reasoning parameters
- Test API responses include reasoning tokens (when not excluded)
- Test per-model routing with different reasoning configs
- Test hybrid mode with reasoning parameters

### Test Data

```python
TEST_CASES = {
    'openai_o_series': [
        ('o4-mini:low', 'o4-mini', 'effort', 'low'),
        ('o4-mini:high', 'o4-mini', 'effort', 'high'),
        ('o3:medium', 'o3', 'effort', 'medium'),
    ],
    'anthropic_thinking': [
        ('claude-opus-4-20250514:4k', 'claude-opus-4-20250514', 'thinking_tokens', 4096),
        ('claude-sonnet-4-20250514:8000', 'claude-sonnet-4-20250514', 'thinking_tokens', 8000),
        ('claude-opus-4-20250514:1k', 'claude-opus-4-20250514', 'thinking_tokens', 1024),
    ],
    'gemini_thinking': [
        ('gemini-2.5-flash-preview-04-17:4k', 'gemini-2.5-flash-preview-04-17', 'thinking_budget', 4096),
        ('gemini-2.5-flash-preview-04-17:16000', 'gemini-2.5-flash-preview-04-17', 'thinking_budget', 16000),
    ]
}
```

## Implementation Notes

### Backward Compatibility

- Models without reasoning suffixes work exactly as before
- Environment variables are optional; system works without them
- Existing model mapping logic remains unchanged
- No breaking changes to API endpoints or request/response formats

### Performance Considerations

- Model name parsing adds minimal overhead (regex + string operations)
- Validation logic is O(1) for range checks
- No additional API calls or external dependencies
- Caching of parsed model names could be added if needed

### Provider-Specific Considerations

**OpenAI**:
- Responses API is preferred but not required
- Fallback to system message approach for older SDKs
- Reasoning tokens may increase response time and cost

**Anthropic**:
- Thinking tokens are only supported on specific Claude 4.x models
- Budget must be within 1024-16000 range
- Thinking tokens appear in response metadata

**Gemini**:
- Thinking budget only supported on gemini-2.5-flash-preview-04-17
- Budget range is 0-24576 (larger than Anthropic)
- Configuration goes in generation_config, not top-level

### Security Considerations

- Validate all user-provided reasoning parameters
- Sanitize model names to prevent injection attacks
- Log reasoning parameter usage for audit trails
- Respect provider rate limits (reasoning may consume more tokens)

## Migration Path

### Phase 1: Core Implementation
1. Create model parser and reasoning validator utilities
2. Extend Model Manager with reasoning capability detection
3. Update Request Converter to apply reasoning parameters
4. Add unit tests for new components

### Phase 2: Configuration
1. Add environment variables to Config class
2. Update .env.example with reasoning configuration
3. Add configuration validation
4. Document environment variables in README

### Phase 3: Integration
1. Test with real API endpoints (OpenAI, Anthropic, Gemini)
2. Verify streaming works with reasoning parameters
3. Test tool use with reasoning parameters
4. Test hybrid mode with per-model reasoning configs

### Phase 4: Documentation
1. Update API documentation with reasoning examples
2. Add reasoning configuration guide
3. Document provider-specific limitations
4. Add troubleshooting section for common issues

## API Examples

### Example 1: OpenAI o-series with High Reasoning Effort

**Request**:
```json
{
  "model": "o4-mini:high",
  "messages": [
    {"role": "user", "content": "Explain quantum entanglement"}
  ],
  "max_tokens": 4096
}
```

**Converted OpenAI Request**:
```json
{
  "model": "o4-mini",
  "messages": [
    {"role": "user", "content": "Explain quantum entanglement"}
  ],
  "max_tokens": 4096,
  "reasoning": {
    "effort": "high"
  }
}
```

### Example 2: Anthropic Claude with 4k Thinking Tokens

**Request**:
```json
{
  "model": "claude-opus-4-20250514:4k",
  "messages": [
    {"role": "user", "content": "Solve this complex math problem..."}
  ],
  "max_tokens": 4096
}
```

**Converted Request**:
```json
{
  "model": "claude-opus-4-20250514",
  "messages": [
    {"role": "user", "content": "Solve this complex math problem..."}
  ],
  "max_tokens": 4096,
  "thinking": {
    "type": "enabled",
    "budget": 4096
  }
}
```

### Example 3: Environment Variable Defaults

**.env Configuration**:
```bash
REASONING_EFFORT="medium"
REASONING_MAX_TOKENS="8000"
BIG_MODEL="o4-mini"
```

**Request** (no suffix):
```json
{
  "model": "claude-opus-4-20250514",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 4096
}
```

**Applied Configuration**:
- Model: claude-opus-4-20250514 (supports thinking tokens)
- Thinking budget: 8000 (from REASONING_MAX_TOKENS)
- No effort level (not applicable to Anthropic)

## References

- [Anthropic Claude API Documentation](https://docs.anthropic.com/en/api/models-list)
- [OpenAI o-series Models Documentation](https://platform.openai.com/docs/guides/reasoning)
- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [just-prompt MCP Server](https://github.com/disler/just-prompt) - Reference implementation
