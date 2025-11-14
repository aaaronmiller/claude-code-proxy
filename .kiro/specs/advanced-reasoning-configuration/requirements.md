# Requirements Document

## Introduction

This feature enhances the Claude-to-OpenAI proxy to support advanced reasoning capabilities for both OpenAI and Anthropic models. It enables fine-grained control over thinking tokens (Anthropic), reasoning effort levels (OpenAI), and thinking budgets (Google Gemini) through configuration and request-level parameters. The implementation will follow the patterns established in the just-prompt MCP server, allowing users to specify reasoning parameters via model name suffixes or configuration settings.

## Glossary

- **Proxy System**: The Claude-to-OpenAI API proxy that converts Claude API requests to OpenAI-compatible formats
- **Thinking Tokens**: Anthropic's extended thinking capability that allows Claude models to perform more thorough reasoning before responding (budget range: 1024-16000 tokens)
- **Reasoning Effort**: OpenAI's o-series parameter that controls internal reasoning depth with levels: low, medium, high
- **Thinking Budget**: Google Gemini's extended thinking capability (budget range: 0-24576)
- **Model Suffix**: A notation appended to model names to specify reasoning parameters (e.g., `:4k`, `:high`)
- **Request Converter**: The component that transforms Claude API requests into OpenAI-compatible format
- **Model Manager**: The component responsible for mapping Claude model names to OpenAI model names and managing model configurations

## Requirements

### Requirement 1

**User Story:** As a developer using the proxy, I want to enable thinking tokens for Anthropic Claude models so that I can get more thorough and well-reasoned responses.

#### Acceptance Criteria

1. WHEN a user specifies a Claude model with a thinking token suffix (e.g., `claude-opus-4-20250514:4k`), THE Proxy System SHALL parse the suffix and extract the thinking token budget
2. WHEN the thinking token budget is specified with k notation (e.g., `1k`, `4k`, `8k`), THE Proxy System SHALL convert it to the exact token count (1024, 4096, 8192)
3. WHEN the thinking token budget is specified as an exact number (e.g., `8000`), THE Proxy System SHALL use that value directly
4. IF the thinking token budget is below 1024, THEN THE Proxy System SHALL adjust it to 1024
5. IF the thinking token budget is above 16000, THEN THE Proxy System SHALL adjust it to 16000
6. WHEN thinking tokens are enabled for a supported Claude model, THE Proxy System SHALL include the thinking configuration in the API request to Anthropic

### Requirement 2

**User Story:** As a developer using the proxy, I want to control reasoning effort for OpenAI o-series models so that I can balance response quality with speed and cost.

#### Acceptance Criteria

1. WHEN a user specifies an OpenAI o-series model with a reasoning effort suffix (e.g., `o4-mini:high`), THE Proxy System SHALL parse the suffix and extract the reasoning effort level
2. WHEN the reasoning effort level is `:low`, THE Proxy System SHALL set the reasoning effort parameter to "low"
3. WHEN the reasoning effort level is `:medium`, THE Proxy System SHALL set the reasoning effort parameter to "medium"
4. WHEN the reasoning effort level is `:high`, THE Proxy System SHALL set the reasoning effort parameter to "high"
5. WHEN no reasoning effort suffix is provided for an o-series model, THE Proxy System SHALL use the default reasoning effort from environment configuration
6. WHEN the OpenAI SDK supports the Responses API, THE Proxy System SHALL use the Responses API endpoint with the reasoning.effort parameter

### Requirement 3

**User Story:** As a developer using the proxy, I want to enable thinking budget for Google Gemini models so that I can leverage extended reasoning capabilities.

#### Acceptance Criteria

1. WHEN a user specifies a Gemini model with a thinking budget suffix (e.g., `gemini-2.5-flash-preview-04-17:4k`), THE Proxy System SHALL parse the suffix and extract the thinking budget
2. WHEN the thinking budget is specified with k notation, THE Proxy System SHALL convert it to the exact token count
3. IF the thinking budget is below 0, THEN THE Proxy System SHALL adjust it to 0
4. IF the thinking budget is above 24576, THEN THE Proxy System SHALL adjust it to 24576
5. WHEN thinking budget is enabled for gemini-2.5-flash-preview-04-17, THE Proxy System SHALL include the thinking configuration in the API request

### Requirement 4

**User Story:** As a system administrator, I want to configure default reasoning parameters via environment variables so that I can set organization-wide defaults without requiring code changes.

#### Acceptance Criteria

1. WHEN the REASONING_EFFORT environment variable is set to "low", "medium", or "high", THE Proxy System SHALL apply that effort level to all reasoning-capable models unless overridden by model suffix
2. WHEN the REASONING_MAX_TOKENS environment variable is set to an integer value, THE Proxy System SHALL use that value as the default thinking token budget for Anthropic models
3. WHEN the REASONING_EXCLUDE environment variable is set to "true", THE Proxy System SHALL exclude reasoning tokens from API responses
4. WHEN environment variables are not set, THE Proxy System SHALL use provider defaults for reasoning parameters
5. WHEN a model suffix specifies reasoning parameters, THE Proxy System SHALL override environment variable defaults with the suffix values

### Requirement 5

**User Story:** As a developer, I want the proxy to automatically detect which models support reasoning capabilities so that reasoning parameters are only applied to compatible models.

#### Acceptance Criteria

1. WHEN a model is identified as an OpenAI o-series model (o1, o3, o4-mini), THE Proxy System SHALL classify it as reasoning-capable
2. WHEN a model is identified as Claude 3.7, Claude 4.x, or Claude 4.1, THE Proxy System SHALL classify it as thinking-token-capable
3. WHEN a model is identified as gemini-2.5-flash-preview-04-17, THE Proxy System SHALL classify it as thinking-budget-capable
4. WHEN reasoning parameters are specified for a non-reasoning-capable model, THE Proxy System SHALL log a warning and omit the reasoning parameters from the request
5. THE Model Manager SHALL maintain a list of reasoning-capable model patterns for automatic detection

### Requirement 6

**User Story:** As a developer, I want clear error messages when reasoning parameters are invalid so that I can quickly correct configuration issues.

#### Acceptance Criteria

1. WHEN an invalid reasoning effort level is specified (not low/medium/high), THE Proxy System SHALL return an error message indicating valid options
2. WHEN an invalid thinking token budget format is provided, THE Proxy System SHALL return an error message with the expected format
3. WHEN reasoning parameters are applied to an incompatible model, THE Proxy System SHALL log a warning with the model name and reasoning capability requirements
4. WHEN thinking token budgets are automatically adjusted to valid ranges, THE Proxy System SHALL log the adjustment with original and adjusted values
5. THE Proxy System SHALL include the model name and reasoning parameters in all error messages for debugging

### Requirement 7

**User Story:** As a developer, I want reasoning parameters to work seamlessly with existing proxy features so that I can combine reasoning with tool use, streaming, and other capabilities.

#### Acceptance Criteria

1. WHEN reasoning parameters are enabled with streaming responses, THE Proxy System SHALL include reasoning tokens in the stream
2. WHEN reasoning parameters are enabled with tool use, THE Proxy System SHALL apply reasoning to both tool selection and response generation
3. WHEN reasoning parameters are enabled with custom system prompts, THE Proxy System SHALL preserve both the system prompt and reasoning configuration
4. WHEN reasoning parameters are enabled with per-model routing (hybrid mode), THE Proxy System SHALL apply the correct reasoning configuration for each model's endpoint
5. THE Request Converter SHALL integrate reasoning parameter parsing before other request transformations
