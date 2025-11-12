import os
import sys

# Configuration
class Config:
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Add Anthropic API key for client validation
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            print("Warning: ANTHROPIC_API_KEY not set. Client API key validation will be disabled.")
        
        self.openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.azure_api_version = os.environ.get("AZURE_API_VERSION")  # For Azure OpenAI
        self.host = os.environ.get("HOST", "0.0.0.0")
        self.port = int(os.environ.get("PORT", "8082"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        self.max_tokens_limit = int(os.environ.get("MAX_TOKENS_LIMIT", "4096"))
        self.min_tokens_limit = int(os.environ.get("MIN_TOKENS_LIMIT", "100"))

        # Optional: Enable/disable OpenRouter model selection in interactive selector
        # Set to "true" to include OpenRouter models (default), "false" to exclude
        self.enable_openrouter_selection = os.environ.get("ENABLE_OPENROUTER_SELECTION", "true").lower() == "true"
        
        # Connection settings
        self.request_timeout = int(os.environ.get("REQUEST_TIMEOUT", "90"))
        self.max_retries = int(os.environ.get("MAX_RETRIES", "2"))
        
        # Model settings - BIG and SMALL models
        self.big_model = os.environ.get("BIG_MODEL", "gpt-4o")
        self.middle_model = os.environ.get("MIDDLE_MODEL", self.big_model)
        self.small_model = os.environ.get("SMALL_MODEL", "gpt-4o-mini")

        # Optional: Per-model routing for hybrid deployments
        # Enable per-model endpoints (set to "true" to enable)
        self.enable_big_endpoint = os.environ.get("ENABLE_BIG_ENDPOINT", "false").lower() == "true"
        self.enable_middle_endpoint = os.environ.get("ENABLE_MIDDLE_ENDPOINT", "false").lower() == "true"
        self.enable_small_endpoint = os.environ.get("ENABLE_SMALL_ENDPOINT", "false").lower() == "true"

        # Per-model endpoints (if enabled above)
        self.big_endpoint = os.environ.get("BIG_ENDPOINT", self.openai_base_url)
        self.middle_endpoint = os.environ.get("MIDDLE_ENDPOINT", self.openai_base_url)
        self.small_endpoint = os.environ.get("SMALL_ENDPOINT", self.openai_base_url)

        # Per-model API keys (if enabled above)
        # If not set, falls back to main OPENAI_API_KEY
        self.big_api_key = os.environ.get("BIG_API_KEY", self.openai_api_key)
        self.middle_api_key = os.environ.get("MIDDLE_API_KEY", self.openai_api_key)
        self.small_api_key = os.environ.get("SMALL_API_KEY", self.openai_api_key)

        # ═══════════════════════════════════════════════════════════════════════════════
        # CUSTOM SYSTEM PROMPTS
        # ═══════════════════════════════════════════════════════════════════════════════

        # Enable custom system prompts for each model
        self.enable_custom_big_prompt = os.environ.get("ENABLE_CUSTOM_BIG_PROMPT", "false").lower() == "true"
        self.enable_custom_middle_prompt = os.environ.get("ENABLE_CUSTOM_MIDDLE_PROMPT", "false").lower() == "true"
        self.enable_custom_small_prompt = os.environ.get("ENABLE_CUSTOM_SMALL_PROMPT", "false").lower() == "true"

        # Custom system prompt files (load from file path, use "path:" prefix)
        self.big_system_prompt_file = os.environ.get("BIG_SYSTEM_PROMPT_FILE", "")
        self.middle_system_prompt_file = os.environ.get("MIDDLE_SYSTEM_PROMPT_FILE", "")
        self.small_system_prompt_file = os.environ.get("SMALL_SYSTEM_PROMPT_FILE", "")

        # Inline system prompts (alternative to files)
        self.big_system_prompt = os.environ.get("BIG_SYSTEM_PROMPT", "")
        self.middle_system_prompt = os.environ.get("MIDDLE_SYSTEM_PROMPT", "")
        self.small_system_prompt = os.environ.get("SMALL_SYSTEM_PROMPT", "")

        # GPT-5 reasoning configuration
        # Options: "low", "medium", "high", or None to disable
        self.reasoning_effort = os.environ.get("REASONING_EFFORT")
        # Verbosity setting for responses (affects how detailed the output is)
        self.verbosity = os.environ.get("VERBOSITY")
        # Whether to exclude reasoning tokens from response (default: false)
        self.reasoning_exclude = os.environ.get("REASONING_EXCLUDE", "false").lower() == "true"
        # Optional: Maximum tokens for reasoning (Anthropic/OpenRouter style)
        # Set to integer (e.g., 2000, 8000) or leave empty for provider default
        reasoning_max_tokens = os.environ.get("REASONING_MAX_TOKENS")
        self.reasoning_max_tokens = int(reasoning_max_tokens) if reasoning_max_tokens else None
        
    def validate_api_key(self):
        """Basic API key validation"""
        if not self.openai_api_key:
            return False
        # Basic format check for OpenAI API keys
        if not self.openai_api_key.startswith('sk-'):
            return False
        return True
        
    def validate_client_api_key(self, client_api_key):
        """Validate client's Anthropic API key"""
        # If no ANTHROPIC_API_KEY is set in the environment, skip validation
        if not self.anthropic_api_key:
            return True
            
        # Check if the client's API key matches the expected value
        return client_api_key == self.anthropic_api_key

try:
    config = Config()
    print(f" Configuration loaded: API_KEY={'*' * 20}..., BASE_URL='{config.openai_base_url}'")
except Exception as e:
    print(f"=4 Configuration Error: {e}")
    sys.exit(1)
