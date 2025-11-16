# Implementation Plan

- [x] 1. Create reasoning configuration data models
  - Create `src/models/reasoning.py` with ReasoningConfig, OpenAIReasoningConfig, AnthropicThinkingConfig, and GeminiThinkingConfig dataclasses
  - Define clear type hints and default values for all configuration fields
  - _Requirements: 1.1, 2.1, 3.1_

- [x] 2. Implement model name parser utility
  - Create `src/utils/model_parser.py` with ParsedModel dataclass and parse_model_name function
  - Implement regex pattern `^(.+?)(?::([^:]+))?$` to extract base model and suffix
  - Add k-notation conversion logic (1k → 1024, 4k → 4096, 8k → 8192, 16k → 16384)
  - Handle exact number suffixes (e.g., :8000, :16000)
  - Detect reasoning type based on model family patterns
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1_

- [x] 3. Implement reasoning parameter validator
  - Create `src/utils/reasoning_validator.py` with validation functions
  - Implement validate_openai_reasoning to check effort levels (low/medium/high)
  - Implement validate_anthropic_thinking to adjust budget to 1024-16000 range
  - Implement validate_gemini_thinking to adjust budget to 0-24576 range
  - Implement is_reasoning_capable_model with pattern matching for all providers
  - Add logging for parameter adjustments and warnings
  - _Requirements: 1.4, 1.5, 2.2, 2.3, 2.4, 3.3, 3.4, 5.1, 5.2, 5.3, 5.4, 6.3, 6.4_

- [x] 4. Extend configuration with reasoning parameters
  - Modify `src/core/config.py` to add reasoning_effort, reasoning_max_tokens, reasoning_exclude, and verbosity properties
  - Add per-model reasoning override properties (big_model_reasoning, middle_model_reasoning, small_model_reasoning)
  - Load reasoning configuration from environment variables with proper defaults
  - Add validation for reasoning configuration values
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5. Enhance Model Manager with reasoning capabilities
  - Modify `src/core/model_manager.py` to add parse_and_map_model method
  - Implement get_model_capabilities method to return reasoning support metadata
  - Define REASONING_CAPABLE_MODELS dictionary with patterns for OpenAI, Anthropic, and Gemini
  - Integrate model_parser utility to extract reasoning parameters from model names
  - Return tuple of (openai_model, reasoning_config) from parse_and_map_model
  - _Requirements: 2.5, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Update Request Converter to apply reasoning parameters
  - Modify `src/conversion/request_converter.py` convert_claude_to_openai function
  - Call model_manager.parse_and_map_model instead of map_claude_model_to_openai
  - Extract reasoning_config from parse_and_map_model result
  - Implement OpenAI o-series reasoning application (check for Responses API support)
  - Implement Anthropic thinking tokens application (add 'thinking' parameter)
  - Implement Gemini thinking budget application (add to generation_config)
  - Merge suffix-based reasoning config with environment variable defaults
  - Add logging for applied reasoning configuration
  - _Requirements: 1.6, 2.5, 2.6, 3.5, 4.5, 5.4, 7.3_

- [x] 7. Update Claude request models for thinking support
  - Modify `src/models/claude.py` ClaudeThinkingConfig to include budget field
  - Ensure ClaudeMessagesRequest and ClaudeTokenCountRequest support thinking parameter
  - Update type hints to match Anthropic API specification
  - _Requirements: 1.1, 1.6_

- [x] 8. Add error handling and validation
  - Add try-catch blocks in model_parser for invalid suffix formats
  - Implement error messages for invalid reasoning effort levels
  - Add warnings for reasoning parameters on incompatible models
  - Log parameter adjustments with original and adjusted values
  - Include model name and reasoning parameters in all error messages
  - _Requirements: 5.4, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Update environment configuration documentation
  - Update `.env.example` with reasoning configuration variables and examples
  - Add comments explaining valid values and ranges for each parameter
  - Include examples for OpenAI, Anthropic, and Gemini reasoning configurations
  - Document per-model reasoning override variables
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 10. Verify streaming compatibility with reasoning
  - Test that reasoning parameters work with streaming responses
  - Ensure reasoning tokens are included in stream when not excluded
  - Verify convert_openai_streaming_to_claude_with_cancellation handles reasoning metadata
  - _Requirements: 7.1_

- [x] 11. Verify tool use compatibility with reasoning
  - Test that reasoning parameters work with tool definitions
  - Ensure reasoning applies to both tool selection and response generation
  - Verify tool results are processed correctly with reasoning enabled
  - _Requirements: 7.2_

- [x] 12. Verify hybrid mode compatibility with reasoning
  - Test per-model routing with different reasoning configurations
  - Ensure BIG_MODEL, MIDDLE_MODEL, and SMALL_MODEL can have different reasoning settings
  - Verify per-model endpoints apply correct reasoning parameters
  - _Requirements: 7.4_

- [x] 13. Create unit tests for model parser
  - Write tests for parse_model_name with various suffix formats
  - Test k-notation conversion (1k, 4k, 8k, 16k)
  - Test exact number suffixes (8000, 16000)
  - Test models without suffixes (backward compatibility)
  - Test invalid suffix formats
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1_

- [x] 14. Create unit tests for reasoning validator
  - Write tests for validate_openai_reasoning with valid and invalid effort levels
  - Test validate_anthropic_thinking with values below, within, and above valid range
  - Test validate_gemini_thinking with values below, within, and above valid range
  - Test is_reasoning_capable_model for all provider patterns
  - Verify logging output for adjustments and warnings
  - _Requirements: 1.4, 1.5, 2.2, 2.3, 2.4, 3.3, 3.4, 5.1, 5.2, 5.3, 5.4_

- [x] 15. Create unit tests for request converter reasoning logic
  - Test reasoning parameter application for OpenAI o-series models
  - Test thinking token application for Anthropic Claude models
  - Test thinking budget application for Gemini models
  - Test environment variable defaults are applied correctly
  - Test suffix overrides environment defaults
  - Test reasoning parameters with streaming enabled
  - Test reasoning parameters with tool definitions
  - _Requirements: 1.6, 2.5, 2.6, 3.5, 4.5, 7.1, 7.2, 7.3_

- [x] 16. Create integration tests for end-to-end reasoning flow
  - Test complete request flow with OpenAI o-series reasoning
  - Test complete request flow with Anthropic thinking tokens
  - Test complete request flow with Gemini thinking budget
  - Test per-model routing with different reasoning configs
  - Test hybrid mode with reasoning parameters
  - Verify API responses include reasoning metadata when expected
  - _Requirements: 7.4_
