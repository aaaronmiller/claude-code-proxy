# Requirements Document

## Introduction

This feature adds intelligent context window management to the Claude-to-OpenAI proxy to prevent token limit errors. When requests exceed the target model's context window, the system will automatically compress the conversation history while preserving critical information.

## Glossary

- **Proxy**: The Claude-to-OpenAI API translation service
- **Context Window**: The maximum number of tokens a model can process in a single request
- **Middle-Out Transform**: OpenRouter's compression technique that preserves the beginning and end of conversations while compressing the middle
- **Token Budget**: The calculated safe limit for a request based on model capacity and desired output length
- **System Message**: The initial instruction message that defines the assistant's behavior
- **Tool Messages**: Messages containing function/tool call results

## Requirements

### Requirement 1

**User Story:** As a proxy user, I want requests to automatically fit within model token limits, so that I don't receive 400 errors for large conversations

#### Acceptance Criteria

1. WHEN the Proxy receives a request exceeding the model's context window, THE Proxy SHALL compress the message history to fit within the token budget
2. THE Proxy SHALL preserve the system message without modification during compression
3. THE Proxy SHALL preserve the most recent user message without modification during compression
4. THE Proxy SHALL preserve all tool-related messages (tool calls and results) during compression
5. WHEN compression is applied, THE Proxy SHALL log the original and compressed token counts

### Requirement 2

**User Story:** As a developer, I want configurable compression strategies, so that I can optimize for my specific use case

#### Acceptance Criteria

1. THE Proxy SHALL support a "middle-out" compression strategy that preserves conversation start and end
2. THE Proxy SHALL support a "sliding-window" compression strategy that preserves only recent messages
3. THE Proxy SHALL allow configuration of the compression strategy via environment variable
4. THE Proxy SHALL default to "middle-out" compression when no strategy is specified
5. THE Proxy SHALL allow configuration of the percentage of context to preserve at conversation start (default 20%)

### Requirement 3

**User Story:** As a proxy administrator, I want automatic token counting, so that compression decisions are accurate

#### Acceptance Criteria

1. THE Proxy SHALL estimate token counts using the tiktoken library for OpenAI models
2. WHEN tiktoken is unavailable for a model, THE Proxy SHALL estimate tokens as text_length / 4
3. THE Proxy SHALL calculate the token budget as (model_max_tokens - max_completion_tokens - safety_buffer)
4. THE Proxy SHALL use a safety buffer of 100 tokens for token count estimation errors
5. THE Proxy SHALL retrieve model context window limits from a model registry or use conservative defaults

### Requirement 4

**User Story:** As a user, I want compression to be transparent, so that I understand when and why it happens

#### Acceptance Criteria

1. WHEN compression occurs, THE Proxy SHALL add a header "X-Context-Compressed" with value "true" to the response
2. WHEN compression occurs, THE Proxy SHALL add a header "X-Original-Tokens" with the pre-compression token count
3. WHEN compression occurs, THE Proxy SHALL add a header "X-Compressed-Tokens" with the post-compression token count
4. THE Proxy SHALL log compression events at INFO level with before/after statistics
5. WHEN compression is insufficient to fit the token budget, THE Proxy SHALL return a 400 error with a clear message

### Requirement 5

**User Story:** As a developer, I want to disable compression for specific requests, so that I can control behavior when needed

#### Acceptance Criteria

1. WHEN a request includes header "X-Disable-Compression" with value "true", THE Proxy SHALL skip compression
2. WHEN compression is disabled and the request exceeds token limits, THE Proxy SHALL forward the request unchanged
3. THE Proxy SHALL allow disabling compression globally via environment variable DISABLE_CONTEXT_COMPRESSION
4. WHEN compression is disabled globally, THE Proxy SHALL log a warning at startup
