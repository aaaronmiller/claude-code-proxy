# Design Document

## Overview

The advanced reasoning configuration system provides comprehensive support for reasoning-capable models with arbitrary token budgets, rich terminal visualization, and performance monitoring.

## Architecture

### Core Components

1. **Reasoning Models** (`src/models/reasoning.py`)
   - OpenAIReasoningConfig: Supports effort-based and max_tokens configuration
   - AnthropicThinkingConfig: Token budget-based configuration
   - GeminiThinkingConfig: Budget-based configuration with validation

2. **Model Parser** (`src/utils/model_parser.py`)
   - Parses model names with suffix notation (model:50k, model:8k)
   - Extracts reasoning configuration from model strings
   - Validates and normalizes token budgets

3. **Reasoning Validator** (`src/utils/reasoning_validator.py`)
   - Validates reasoning parameters against model capabilities
   - Adjusts token budgets to fit within model limits
   - Provides error handling and fallback values

4. **Request Logger** (`src/utils/request_logger.py`)
   - Rich colored terminal output with session-based colors
   - Progress bars for token usage visualization
   - Performance metrics display (tokens/sec, latency)
   - Fallback to plain text when Rich unavailable

5. **Model Limits Database** (`src/utils/model_limits.py`)
   - Comprehensive database of 100+ models
   - Context window and output limits
   - Auto-scraping from OpenRouter API
   - Caching and persistence

## Components and Interfaces

### Reasoning Configuration Interface

```python
@dataclass
class ReasoningConfig:
    """Base class for reasoning configurations."""
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        pass
    
    def to_api_params(self) -> Dict[str, Any]:
        """Convert to API parameters."""
        pass
```

### Model Parser Interface

```python
class ModelParser:
    """Parses model names with reasoning suffixes."""
    
    def parse_model_with_reasoning(self, model_string: str) -> Tuple[str, Optional[ReasoningConfig]]:
        """Parse model:suffix notation into model name and reasoning config."""
        pass
    
    def extract_token_budget(self, suffix: str) -> int:
        """Extract token budget from suffix (e.g., '8k' -> 8000)."""
        pass
```

### Request Logger Interface

```python
class RequestLogger:
    """Rich terminal logging with progress visualization."""
    
    def log_request_start(self, request_id: str, model: str, **kwargs):
        """Log request initiation with model routing info."""
        pass
    
    def log_request_complete(self, request_id: str, usage: Dict, **kwargs):
        """Log completion with token usage and performance metrics."""
        pass
    
    def create_progress_bar(self, used: int, total: int) -> str:
        """Create ASCII progress bar for token usage."""
        pass
```

## Data Models

### Reasoning Configurations

```python
@dataclass
class OpenAIReasoningConfig(ReasoningConfig):
    effort: Optional[str] = None  # "low", "medium", "high"
    max_tokens: Optional[int] = None  # Direct token specification
    
@dataclass 
class AnthropicThinkingConfig(ReasoningConfig):
    budget: int  # Token budget (1024-32000)
    
@dataclass
class GeminiThinkingConfig(ReasoningConfig):
    budget: int  # Token budget with validation
```

### Model Limits

```python
@dataclass
class ModelLimits:
    context_window: int
    output_limit: int
    supports_reasoning: bool
    provider: str
    cost_per_1m_tokens: Optional[float]
```

## Error Handling

### Validation Errors
- Invalid token budgets are adjusted to valid ranges
- Unsupported reasoning configurations fall back to defaults
- Model parsing errors return base model without reasoning

### Runtime Errors
- Rich library unavailable: fallback to plain text logging
- Model limits unavailable: use conservative defaults
- API errors: graceful degradation with error logging

## Testing Strategy

### Unit Tests
- Reasoning configuration validation
- Model name parsing with various suffix formats
- Token budget extraction and normalization
- Progress bar generation and formatting

### Integration Tests
- End-to-end reasoning request flow
- Terminal output with actual API responses
- Model limits database loading and querying
- Error handling with invalid configurations

### Performance Tests
- Large token budget handling
- Terminal output performance with high request volume
- Model database lookup performance