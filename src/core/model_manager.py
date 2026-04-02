import logging
from typing import Optional, Tuple, Dict, Any
from src.core.config import config
from src.services.models.model_parser import parse_model_name, ParsedModel
from src.core.reasoning_validator import (
    validate_openai_reasoning,
    validate_anthropic_thinking,
    validate_gemini_thinking,
    is_reasoning_capable_model,
    _is_openai_reasoning_model,
)
from src.models.reasoning import (
    ReasoningConfig,
    OpenAIReasoningConfig,
    AnthropicThinkingConfig,
    GeminiThinkingConfig,
)


logger = logging.getLogger(__name__)

# Reasoning type metadata (no hardcoded model patterns — detection is in reasoning_validator)
REASONING_TYPE_META = {
    "effort": {"default_effort": "medium"},
    "thinking_tokens": {"min_tokens": 1024, "max_tokens": 128000},
    "thinking_budget": {"min_budget": 0, "max_budget": 24576},
}


class ModelManager:
    def __init__(self, config):
        self.config = config

    def is_newer_openai_model(self, model_name: str) -> bool:
        """
        Check if the model is a newer OpenAI reasoning model (o1, o3, o4, gpt-5).
        These models require max_completion_tokens instead of max_tokens and temperature=1.

        Args:
            model_name: Model name to check

        Returns:
            True if the model is o1, o3, o4, or gpt-5
        """
        model_lower = model_name.lower()

        # Check for o-series models (o1, o3, o4)
        if any(
            pattern in model_lower
            for pattern in ["o1-", "o1mini", "o3-", "o3mini", "o4-", "o4mini"]
        ):
            return True

        # Check for gpt-5
        if "gpt-5" in model_lower or "gpt5" in model_lower:
            return True

        return False

    def is_o3_model(self, model_name: str) -> bool:
        """
        Check if the model is an OpenAI o3 model.

        Args:
            model_name: Model name to check

        Returns:
            True if the model is an o3 variant
        """
        model_lower = model_name.lower()
        return "o3-" in model_lower or "o3mini" in model_lower

    def map_claude_model_to_openai(self, claude_model: str) -> str:
        """Map Claude model names to OpenAI model names based on BIG/SMALL pattern.

        Only maps Claude-specific model family names (haiku/sonnet/opus).
        All other model names — including Gemini, OpenAI, custom, or
        provider-prefixed models — pass through as-is.
        
        Handles hybrid tier/provider format:
        - 'opus/qwen-2.5-72b' → returns 'qwen-2.5-72b' (uses provider model directly)
        - 'sonnet/openai/gpt-4o' → returns 'openai/gpt-4o' (uses provider model directly)
        """
        model_lower = claude_model.lower()

        # Check for hybrid tier/provider format first (e.g., opus/qwen-2.5, sonnet/openai/gpt-4o)
        if "/" in model_lower:
            parts = model_lower.split("/", 1)
            if parts[0] in ["opus", "sonnet", "haiku"]:
                # This is tier/provider-model format, return the provider-model part
                # The actual model ID after the tier prefix
                provider_model = parts[1]
                logger.debug(f"Hybrid model detected: '{claude_model}' → using '{provider_model}'")
                return provider_model

        # Only map Claude-specific model names by family keyword
        if "haiku" in model_lower:
            return self.config.small_model
        elif "sonnet" in model_lower:
            return self.config.middle_model
        elif "opus" in model_lower:
            return self.config.big_model
        else:
            # Pass through all other models as-is (Gemini, OpenAI, OpenRouter, custom, etc.)
            return claude_model

    def parse_and_map_model(
        self, claude_model: str
    ) -> Tuple[str, Optional[ReasoningConfig]]:
        """
        Parse model name with reasoning suffix and map to OpenAI model.

        Args:
            claude_model: Claude model name with optional reasoning suffix

        Returns:
            Tuple of (openai_model, reasoning_config)
            - openai_model: Mapped OpenAI model name
            - reasoning_config: ReasoningConfig object or None
        """
        # Parse model name for reasoning suffix
        parsed = parse_model_name(claude_model)

        # Map base model to OpenAI model
        openai_model = self.map_claude_model_to_openai(parsed.base_model)

        # If no reasoning parameters, return early
        if not parsed.reasoning_type or parsed.reasoning_value is None:
            # Check for environment variable defaults
            reasoning_config = self._get_default_reasoning_config(openai_model)
            return openai_model, reasoning_config

        # Create reasoning config based on type
        reasoning_config = self._create_reasoning_config(
            parsed.reasoning_type, parsed.reasoning_value, openai_model
        )

        logger.info(
            f"Parsed model '{claude_model}' → base='{openai_model}', "
            f"reasoning_type='{parsed.reasoning_type}', "
            f"reasoning_value={parsed.reasoning_value}"
        )

        return openai_model, reasoning_config

    def _get_default_reasoning_config(
        self, model_name: str
    ) -> Optional[ReasoningConfig]:
        """
        Get default reasoning configuration from environment variables.

        Args:
            model_name: Model name to check for reasoning capability

        Returns:
            ReasoningConfig object or None
        """
        # Check if model supports reasoning
        is_capable, reasoning_type = is_reasoning_capable_model(model_name)

        if not is_capable:
            return None

        # Get default effort from config
        default_effort = self.config.reasoning_effort
        default_max_tokens = self.config.reasoning_max_tokens

        if reasoning_type == "effort" and default_effort:
            try:
                validated_effort = validate_openai_reasoning(default_effort)
                return OpenAIReasoningConfig(
                    enabled=True,
                    effort=validated_effort,
                    exclude=self.config.reasoning_exclude,
                )
            except ValueError as e:
                logger.warning(f"Invalid default reasoning effort: {e}")
                return None

        elif reasoning_type == "thinking_tokens" and default_max_tokens:
            validated_budget = validate_anthropic_thinking(default_max_tokens)
            return AnthropicThinkingConfig(type="enabled", budget=validated_budget)

        elif reasoning_type == "thinking_budget" and default_max_tokens:
            validated_budget = validate_gemini_thinking(default_max_tokens)
            return GeminiThinkingConfig(budget=validated_budget)

        return None

    def _create_reasoning_config(
        self, reasoning_type: str, reasoning_value: Any, model_name: str
    ) -> Optional[ReasoningConfig]:
        """
        Create reasoning configuration based on type and value.

        Args:
            reasoning_type: Type of reasoning ('effort', 'thinking_tokens', 'thinking_budget')
            reasoning_value: Value for reasoning parameter
            model_name: Model name for validation

        Returns:
            ReasoningConfig object or None
        """
        try:
            if reasoning_type == "effort":
                validated_effort = validate_openai_reasoning(str(reasoning_value))
                return OpenAIReasoningConfig(
                    enabled=True,
                    effort=validated_effort,
                    max_tokens=None,
                    exclude=self.config.reasoning_exclude,
                )

            elif reasoning_type == "thinking_tokens":
                # Check if this is for OpenAI (arbitrary token budget) or Anthropic
                is_openai = _is_openai_reasoning_model(model_name.lower())

                if is_openai:
                    # OpenAI with arbitrary token budget
                    return OpenAIReasoningConfig(
                        enabled=True,
                        effort=None,
                        max_tokens=int(reasoning_value),
                        exclude=self.config.reasoning_exclude,
                    )
                else:
                    # Anthropic thinking tokens
                    validated_budget = validate_anthropic_thinking(int(reasoning_value))
                    return AnthropicThinkingConfig(
                        type="enabled", budget=validated_budget
                    )

            elif reasoning_type == "thinking_budget":
                validated_budget = validate_gemini_thinking(int(reasoning_value))
                return GeminiThinkingConfig(budget=validated_budget)

        except (ValueError, TypeError) as e:
            logger.error(
                f"Failed to create reasoning config for model '{model_name}': {e}"
            )
            return None

        return None

    def get_model_capabilities(self, model_name: str) -> Dict[str, Any]:
        """
        Get model capabilities including reasoning support.

        Args:
            model_name: Model name to check

        Returns:
            Dictionary with capability information:
            {
                'supports_reasoning': bool,
                'reasoning_type': str,
                'max_reasoning_tokens': int,
                'default_reasoning': Optional[ReasoningConfig]
            }
        """
        is_capable, reasoning_type = is_reasoning_capable_model(model_name)

        capabilities = {
            "supports_reasoning": is_capable,
            "reasoning_type": reasoning_type,
            "max_reasoning_tokens": None,
            "default_reasoning": None,
        }

        if not is_capable:
            return capabilities

        # Get max tokens based on reasoning type
        if reasoning_type == "thinking_tokens":
            capabilities["max_reasoning_tokens"] = REASONING_TYPE_META[
                "thinking_tokens"
            ]["max_tokens"]
        elif reasoning_type == "thinking_budget":
            capabilities["max_reasoning_tokens"] = REASONING_TYPE_META[
                "thinking_budget"
            ]["max_budget"]

        # Get default reasoning config
        capabilities["default_reasoning"] = self._get_default_reasoning_config(
            model_name
        )

        return capabilities


model_manager = ModelManager(config)
