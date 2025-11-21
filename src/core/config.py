import os
import sys

# Configuration
class Config:
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

        # Determine operating mode: proxy (default) or passthrough
        # Proxy mode: Server-configured OPENAI_API_KEY handles all requests
        # Passthrough mode: Users supply their own OpenAI API keys via headers
        self.passthrough_mode = False

        if not self.openai_api_key:
            # No server API key configured - enable passthrough mode
            print("INFO: OPENAI_API_KEY not configured - enabling passthrough mode")
            print("INFO: Users must provide their own OpenAI API keys via request headers")
            self.passthrough_mode = True
        elif self.openai_api_key == "pass" or self.openai_api_key == "your-api-key-here" or "your-" in self.openai_api_key.lower() or self.openai_api_key == "sk-your-openai-api-key-here":
            print("WARNING: OPENAI_API_KEY is set to a placeholder value")
            print("INFO: Enabling passthrough mode - users must provide their own API keys")
            self.passthrough_mode = True
            self.openai_api_key = None

        # Set base URL
        self.openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Add Anthropic API key for client validation
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
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

        # ═══════════════════════════════════════════════════════════════════════════════
        # REASONING CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════════════════
        
        # Global reasoning effort level for OpenAI o-series models
        # Options: "low", "medium", "high", or None to disable
        self.reasoning_effort = os.environ.get("REASONING_EFFORT")
        
        # Verbosity setting for responses (affects how detailed the output is)
        self.verbosity = os.environ.get("VERBOSITY")
        
        # Whether to exclude reasoning tokens from response (default: false)
        self.reasoning_exclude = os.environ.get("REASONING_EXCLUDE", "false").lower() == "true"
        
        # Maximum tokens for reasoning/thinking (Anthropic/Gemini style)
        # Set to integer (e.g., 2000, 8000) or leave empty for provider default
        # Valid ranges: Anthropic (1024-16000), Gemini (0-24576)
        reasoning_max_tokens = os.environ.get("REASONING_MAX_TOKENS")
        self.reasoning_max_tokens = int(reasoning_max_tokens) if reasoning_max_tokens else None
        
        # Per-model reasoning overrides (optional)
        # These override the global reasoning_effort for specific models
        self.big_model_reasoning = os.environ.get("BIG_MODEL_REASONING")
        self.middle_model_reasoning = os.environ.get("MIDDLE_MODEL_REASONING")
        self.small_model_reasoning = os.environ.get("SMALL_MODEL_REASONING")
        
        # Validate reasoning configuration
        self._validate_reasoning_config()

        # ═══════════════════════════════════════════════════════════════════════════════
        # TERMINAL DASHBOARD CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════════════════

        # Enable terminal dashboard (default: false)
        self.enable_dashboard = os.environ.get("ENABLE_DASHBOARD", "false").lower() == "true"

        # Dashboard layout: "default", "compact", "detailed"
        self.dashboard_layout = os.environ.get("DASHBOARD_LAYOUT", "default")

        # Dashboard refresh rate in seconds (default: 0.5 = 2 updates per second)
        self.dashboard_refresh = float(os.environ.get("DASHBOARD_REFRESH", "0.5"))

        # Dashboard waterfall size (number of completed requests to show)
        self.dashboard_waterfall_size = int(os.environ.get("DASHBOARD_WATERFALL_SIZE", "20"))

        # Enable usage tracking for dashboard metrics (default: true if dashboard enabled)
        self.track_usage = os.environ.get("TRACK_USAGE", "true" if self.enable_dashboard else "false").lower() == "true"

        # Compact logger mode - reduce console noise when dashboard is active
        self.compact_logger = os.environ.get("COMPACT_LOGGER", "true" if self.enable_dashboard else "false").lower() == "true"

        # ═══════════════════════════════════════════════════════════════════════════════
        # TERMINAL OUTPUT CONFIGURATION (like prompt injection system)
        # ═══════════════════════════════════════════════════════════════════════════════

        # Terminal output display mode: "minimal", "normal", "detailed", "debug"
        # - minimal: Request ID + model only
        # - normal: Request ID + model + tokens + speed (default)
        # - detailed: All metrics including context %, task type, cost
        # - debug: Everything including system flags and client info
        self.terminal_display_mode = os.environ.get("TERMINAL_DISPLAY_MODE", "detailed").lower()

        # Show specific metrics (can be toggled individually)
        self.terminal_show_workspace = os.environ.get("TERMINAL_SHOW_WORKSPACE", "true").lower() == "true"
        self.terminal_show_context_pct = os.environ.get("TERMINAL_SHOW_CONTEXT_PCT", "true").lower() == "true"
        self.terminal_show_task_type = os.environ.get("TERMINAL_SHOW_TASK_TYPE", "true").lower() == "true"
        self.terminal_show_speed = os.environ.get("TERMINAL_SHOW_SPEED", "true").lower() == "true"
        self.terminal_show_cost = os.environ.get("TERMINAL_SHOW_COST", "true").lower() == "true"
        self.terminal_show_duration_colors = os.environ.get("TERMINAL_SHOW_DURATION_COLORS", "true").lower() == "true"

        # Color scheme for terminal output: "auto", "vibrant", "subtle", "mono"
        # - auto: Rich colors with session differentiation (default)
        # - vibrant: Bright, high-contrast colors
        # - subtle: Muted colors for less distraction
        # - mono: Minimal colors, mostly white/gray
        self.terminal_color_scheme = os.environ.get("TERMINAL_COLOR_SCHEME", "auto").lower()

        # Session color differentiation (use different colors per Claude Code session)
        self.terminal_session_colors = os.environ.get("TERMINAL_SESSION_COLORS", "true").lower() == "true"

    def _validate_reasoning_config(self):
        """Validate reasoning configuration values"""
        valid_effort_levels = {'low', 'medium', 'high'}
        
        # Validate global reasoning effort
        if self.reasoning_effort and self.reasoning_effort.lower() not in valid_effort_levels:
            print(f"Warning: Invalid REASONING_EFFORT '{self.reasoning_effort}'. "
                  f"Valid options: {', '.join(sorted(valid_effort_levels))}. Ignoring.")
            self.reasoning_effort = None
        
        # Validate per-model reasoning overrides
        for model_type, reasoning_value in [
            ('BIG_MODEL_REASONING', self.big_model_reasoning),
            ('MIDDLE_MODEL_REASONING', self.middle_model_reasoning),
            ('SMALL_MODEL_REASONING', self.small_model_reasoning)
        ]:
            if reasoning_value and reasoning_value.lower() not in valid_effort_levels:
                print(f"Warning: Invalid {model_type} '{reasoning_value}'. "
                      f"Valid options: {', '.join(sorted(valid_effort_levels))}. Ignoring.")
                # Set to None to ignore invalid value
                if model_type == 'BIG_MODEL_REASONING':
                    self.big_model_reasoning = None
                elif model_type == 'MIDDLE_MODEL_REASONING':
                    self.middle_model_reasoning = None
                elif model_type == 'SMALL_MODEL_REASONING':
                    self.small_model_reasoning = None
        
        # Validate reasoning_max_tokens range
        if self.reasoning_max_tokens is not None:
            if self.reasoning_max_tokens < 0:
                print(f"Warning: REASONING_MAX_TOKENS {self.reasoning_max_tokens} is negative. "
                      f"Setting to 0.")
                self.reasoning_max_tokens = 0
            elif self.reasoning_max_tokens > 24576:
                print(f"Warning: REASONING_MAX_TOKENS {self.reasoning_max_tokens} exceeds maximum (24576). "
                      f"Will be adjusted per provider limits.")
    
    def validate_api_key(self, api_key: str = None):
        """
        Validate OpenAI API key format.

        Args:
            api_key: API key to validate. If None, uses self.openai_api_key

        Returns:
            True if valid, False otherwise
        """
        key_to_validate = api_key if api_key is not None else self.openai_api_key

        if not key_to_validate:
            return False

        # Basic format check for OpenAI API keys
        if not key_to_validate.startswith('sk-'):
            return False

        # Minimum length check (OpenAI keys are typically 48+ characters)
        if len(key_to_validate) < 20:
            return False

        return True
        
    def validate_client_api_key(self, client_api_key):
        """Validate client's Anthropic API key"""
        # If no ANTHROPIC_API_KEY is set in environment, skip validation
        if not self.anthropic_api_key:
            return True
            
        # Check if the client's API key matches the expected value
        return client_api_key == self.anthropic_api_key
    
    def get_custom_headers(self):
        """Get custom headers from environment variables"""
        custom_headers = {}
        
        # Get all environment variables
        env_vars = dict(os.environ)
        
        # Find CUSTOM_HEADER_* environment variables
        for env_key, env_value in env_vars.items():
            if env_key.startswith('CUSTOM_HEADER_'):
                # Convert CUSTOM_HEADER_KEY to Header-Key
                # Remove 'CUSTOM_HEADER_' prefix and convert to header format
                header_name = env_key[14:]  # Remove 'CUSTOM_HEADER_' prefix
                
                if header_name:  # Make sure it's not empty
                    # Convert underscores to hyphens for HTTP header format
                    header_name = header_name.replace('_', '-')
                    custom_headers[header_name] = env_value
        
        return custom_headers

try:
    config = Config()
except Exception as e:
    print(f"Configuration Error: {e}")
    sys.exit(1)
