import os
import sys
import re
from typing import Dict, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# API KEY FORMAT PATTERNS BY PROVIDER
# ═══════════════════════════════════════════════════════════════════════════════
# Each provider has specific key format patterns for validation

API_KEY_PATTERNS: Dict[str, re.Pattern] = {
    'openai': re.compile(r'^sk-[a-zA-Z0-9]{20,}$'),
    'openrouter': re.compile(r'^sk-or-v1-[a-f0-9]{64}$'),  # OpenRouter format
    'anthropic': re.compile(r'^sk-ant-[a-zA-Z0-9\-_]{20,}$'),
    'google': re.compile(r'^AIza[a-zA-Z0-9_-]{35}$'),
    'gemini': re.compile(r'^AIza[a-zA-Z0-9_-]{35}$'),
    'azure': re.compile(r'^[a-f0-9]{32}$'),
    'vibeproxy': re.compile(r'^ya29\.[a-zA-Z0-9_-]+$'),  # OAuth tokens
}

# Provider status cache (populated on startup)
_provider_status_cache: Dict[str, dict] = {}


def validate_api_key_format(key: str, provider: str = None) -> Tuple[bool, str]:
    """
    Validate API key format for a specific provider.

    Args:
        key: The API key to validate
        provider: Optional provider name (openai, openrouter, anthropic, google, azure)
                 If not specified, tries to auto-detect from key format

    Returns:
        Tuple of (is_valid, message)
    """
    if not key:
        return False, "No API key provided"

    # Auto-detect provider from key format if not specified
    if not provider:
        if key.startswith('sk-or-'):
            provider = 'openrouter'
        elif key.startswith('sk-ant-'):
            provider = 'anthropic'
        elif key.startswith('AIza'):
            provider = 'google'
        elif key.startswith('ya29.'):
            provider = 'vibeproxy'
        elif key.startswith('sk-'):
            provider = 'openai'
        elif len(key) == 32 and all(c in '0123456789abcdef' for c in key.lower()):
            provider = 'azure'
        else:
            # Unknown format - accept but warn
            if len(key) >= 20:
                return True, "Unknown key format (accepted)"
            return False, "Key too short (minimum 20 characters)"

    # Validate against provider-specific pattern
    pattern = API_KEY_PATTERNS.get(provider.lower())
    if pattern:
        if pattern.match(key):
            return True, f"Valid {provider} key format"
        else:
            # Check for common issues
            if provider == 'openrouter' and key.startswith('sk-or-'):
                return True, f"Valid OpenRouter key (relaxed validation)"
            elif provider in ('google', 'gemini') and key.startswith('AIza'):
                return True, f"Valid Google key (relaxed validation)"
            return False, f"Invalid {provider} key format"

    # No pattern for this provider - accept if reasonable length
    if len(key) >= 10:
        return True, f"Accepted key for {provider}"
    return False, "Key too short"


def get_provider_status_cache() -> Dict[str, dict]:
    """Get cached provider status from startup validation."""
    return _provider_status_cache


def set_provider_status(provider: str, status: dict):
    """Update provider status in cache."""
    _provider_status_cache[provider] = status


# Configuration
class Config:
    def __init__(self):
        # ═══════════════════════════════════════════════════════════════════════════════
        # SEMANTIC ENVIRONMENT VARIABLE NAMES (NEW)
        # ═══════════════════════════════════════════════════════════════════════════════
        # Use semantic names that represent what they actually do:
        # - PROVIDER_API_KEY: API key for your backend provider (OpenRouter, OpenAI, etc.)
        # - PROVIDER_BASE_URL: Base URL for your backend provider
        # - PROXY_AUTH_KEY: Optional authentication key for proxy clients
        #
        # Legacy names (OPENAI_API_KEY, OPENAI_BASE_URL, ANTHROPIC_API_KEY) are still
        # supported for backward compatibility but will show deprecation warnings.
        # ═══════════════════════════════════════════════════════════════════════════════

        # Check for new semantic variable names first, fall back to legacy names
        provider_api_key = os.environ.get("PROVIDER_API_KEY")
        provider_base_url = os.environ.get("PROVIDER_BASE_URL")
        proxy_auth_key = os.environ.get("PROXY_AUTH_KEY")

        # Legacy variable support with deprecation warnings
        legacy_openai_key = os.environ.get("OPENAI_API_KEY")
        legacy_openai_url = os.environ.get("OPENAI_BASE_URL")
        legacy_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        # Determine which values to use (new takes precedence)
        if provider_api_key:
            self.openai_api_key = provider_api_key
        elif legacy_openai_key:
            self.openai_api_key = legacy_openai_key
            # print("⚠️  DEPRECATION WARNING: OPENAI_API_KEY is deprecated. Use PROVIDER_API_KEY instead.")
            # print("   This variable name is misleading - it works with ANY provider, not just OpenAI.")
        else:
            self.openai_api_key = None

        if provider_base_url:
            self.openai_base_url = provider_base_url
        elif legacy_openai_url:
            self.openai_base_url = legacy_openai_url
            # print("⚠️  DEPRECATION WARNING: OPENAI_BASE_URL is deprecated. Use PROVIDER_BASE_URL instead.")
        else:
            self.openai_base_url = "https://api.openai.com/v1"

        if proxy_auth_key:
            self.anthropic_api_key = proxy_auth_key
        elif legacy_anthropic_key:
            self.anthropic_api_key = legacy_anthropic_key
            # print("⚠️  DEPRECATION WARNING: ANTHROPIC_API_KEY is deprecated. Use PROXY_AUTH_KEY instead.")
            # print("   This variable is for proxy authentication, NOT for Anthropic's API.")
        else:
            self.anthropic_api_key = None

        # Determine operating mode: proxy (default) or passthrough
        # Proxy mode: Server-configured PROVIDER_API_KEY handles all requests
        # Passthrough mode: Users supply their own API keys via headers
        self.passthrough_mode = False

        if not self.openai_api_key:
            # No server API key configured - enable passthrough mode
            print("INFO: PROVIDER_API_KEY not configured - enabling passthrough mode")
            print("INFO: Users must provide their own API keys via request headers")
            self.passthrough_mode = True
        elif self.openai_api_key == "pass" or self.openai_api_key == "your-api-key-here" or "your-" in self.openai_api_key.lower() or self.openai_api_key == "sk-your-openai-api-key-here":
            print("WARNING: PROVIDER_API_KEY is set to a placeholder value")
            print("INFO: Enabling passthrough mode - users must provide their own API keys")
            self.passthrough_mode = True
            self.openai_api_key = None
        
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

        # ═══════════════════════════════════════════════════════════════════════════════
        # MODEL CASCADE (Fallback on provider errors)
        # ═══════════════════════════════════════════════════════════════════════════════
        # Enable with MODEL_CASCADE=true
        # Comma-separated fallback models in format: provider/model
        self.model_cascade = os.environ.get("MODEL_CASCADE", "false").lower() == "true"
        self.big_cascade = self._parse_cascade(os.environ.get("BIG_CASCADE", ""))
        self.middle_cascade = self._parse_cascade(os.environ.get("MIDDLE_CASCADE", ""))
        self.small_cascade = self._parse_cascade(os.environ.get("SMALL_CASCADE", ""))

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
        # CRITICAL: Each endpoint MUST have its own API key if routing to different providers
        # Do NOT fallback to main provider key - that causes auth failures
        
        # BIG endpoint key validation
        big_key_from_env = os.environ.get("BIG_API_KEY")
        if self.enable_big_endpoint:
            if big_key_from_env:
                self.big_api_key = big_key_from_env
            elif self.big_endpoint != self.openai_base_url:
                # Different endpoint but no key - defer to auto-detection
                self.big_api_key = None
            else:
                self.big_api_key = self.openai_api_key
        else:
            self.big_api_key = self.openai_api_key
        
        # MIDDLE endpoint key validation  
        middle_key_from_env = os.environ.get("MIDDLE_API_KEY")
        if self.enable_middle_endpoint:
            if middle_key_from_env:
                self.middle_api_key = middle_key_from_env
            elif self.middle_endpoint != self.openai_base_url:
                # Different endpoint but no key - defer to auto-detection
                self.middle_api_key = None
            else:
                self.middle_api_key = self.openai_api_key
        else:
            self.middle_api_key = self.openai_api_key
            
        # SMALL endpoint key validation
        small_key_from_env = os.environ.get("SMALL_API_KEY")
        if self.enable_small_endpoint:
            if small_key_from_env:
                self.small_api_key = small_key_from_env
            elif self.small_endpoint != self.openai_base_url:
                # Different endpoint but no key - defer to auto-detection
                self.small_api_key = None
            else:
                self.small_api_key = self.openai_api_key
        else:
            self.small_api_key = self.openai_api_key


        # ═══════════════════════════════════════════════════════════════════════════════
        # PROVIDER DETECTION (Auto-detected from URLs, can be overridden)
        # ═══════════════════════════════════════════════════════════════════════════════
        # Providers: gemini, openrouter, openai, anthropic, azure, openai_compatible
        # Auto-detection analyzes the endpoint URLs to determine the provider
        # Override with explicit values if auto-detection is incorrect
        
        from src.services.providers.provider_detector import detect_provider
        
        # Detect providers for each endpoint
        self.default_provider = os.environ.get(
            "DEFAULT_PROVIDER", 
            detect_provider(self.openai_base_url)
        )
        self.big_provider = os.environ.get(
            "BIG_PROVIDER",
            detect_provider(self.big_endpoint) if self.enable_big_endpoint else self.default_provider
        )
        self.middle_provider = os.environ.get(
            "MIDDLE_PROVIDER",
            detect_provider(self.middle_endpoint) if self.enable_middle_endpoint else self.default_provider
        )
        self.small_provider = os.environ.get(
            "SMALL_PROVIDER",
            detect_provider(self.small_endpoint) if self.enable_small_endpoint else self.default_provider
        )
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # AUTO API KEY LOOKUP BY PROVIDER
        # ═══════════════════════════════════════════════════════════════════════════════
        # If no explicit API key is set for an endpoint, look up by detected provider
        # Provider -> Environment Variable mapping:
        #   openrouter -> OPENROUTER_API_KEY
        #   openai -> OPENAI_API_KEY  
        #   anthropic -> ANTHROPIC_API_KEY
        #   google/gemini -> GOOGLE_API_KEY or GEMINI_API_KEY
        #   azure -> AZURE_API_KEY
        
        provider_key_map = {
            "openrouter": os.environ.get("OPENROUTER_API_KEY"),
            "openai": os.environ.get("OPENAI_API_KEY"),
            "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
            "google": os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"),
            "gemini": os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"),
            "azure": os.environ.get("AZURE_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY"),
            "vibeproxy": self.openai_api_key,  # VibeProxy uses main provider key (Antigravity token)
            "local": "dummy",  # Local endpoints don't need auth
        }
        
        # Auto-assign API keys based on detected provider if not explicitly set
        if self.enable_big_endpoint and self.big_api_key is None:
            auto_key = provider_key_map.get(self.big_provider.lower())
            if auto_key:
                print(f"✅ AUTO: Using {self.big_provider.upper()}_API_KEY for BIG endpoint")
                self.big_api_key = auto_key
            else:
                print(f"⚠️  WARNING: BIG endpoint enabled but no API key found")
                print(f"   → Set BIG_API_KEY or {self.big_provider.upper()}_API_KEY in .env")
                
        if self.enable_middle_endpoint and self.middle_api_key is None:
            auto_key = provider_key_map.get(self.middle_provider.lower())
            if auto_key:
                print(f"✅ AUTO: Using {self.middle_provider.upper()}_API_KEY for MIDDLE endpoint")
                self.middle_api_key = auto_key
            else:
                print(f"⚠️  WARNING: MIDDLE endpoint enabled but no API key found")
                print(f"   → Set MIDDLE_API_KEY or {self.middle_provider.upper()}_API_KEY in .env")
                
        if self.enable_small_endpoint and self.small_api_key is None:
            auto_key = provider_key_map.get(self.small_provider.lower())
            if auto_key:
                print(f"✅ AUTO: Using {self.small_provider.upper()}_API_KEY for SMALL endpoint")
                self.small_api_key = auto_key
            else:
                print(f"⚠️  WARNING: SMALL endpoint enabled but no API key found")
                print(f"   → Set SMALL_API_KEY or {self.small_provider.upper()}_API_KEY in .env")



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
            elif self.reasoning_max_tokens > 131072:
                print(f"Warning: REASONING_MAX_TOKENS {self.reasoning_max_tokens} exceeds maximum (131072). "
                      f"Will be adjusted per provider limits.")
    
    def validate_api_key(self, api_key: str = None, provider: str = None) -> bool:
        """
        Validate API key format with provider-aware validation.

        Args:
            api_key: API key to validate. If None, uses self.openai_api_key
            provider: Optional provider name for format validation

        Returns:
            True if valid, False otherwise
        """
        key_to_validate = api_key if api_key is not None else self.openai_api_key

        if not key_to_validate:
            return False

        # Use provider-aware validation
        is_valid, _ = validate_api_key_format(key_to_validate, provider)
        return is_valid
        
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
    
    def _parse_cascade(self, cascade_str: str) -> list:
        """Parse comma-separated cascade list into list of model strings."""
        if not cascade_str:
            return []
        return [m.strip() for m in cascade_str.split(",") if m.strip()]
    
    def get_cascade_for_tier(self, tier: str) -> list:
        """Get cascade list for a model tier (big, middle, small)."""
        cascades = {
            "big": self.big_cascade,
            "middle": self.middle_cascade,
            "small": self.small_cascade
        }
        return cascades.get(tier.lower(), [])

try:
    config = Config()
except Exception as e:
    print(f"Configuration Error: {e}")
    sys.exit(1)
