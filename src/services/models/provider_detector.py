"""Provider detection and model name normalization."""

import re
from typing import Tuple, Optional
from urllib.parse import urlparse


class ProviderDetector:
    """Detect provider from base URL and normalize model names accordingly."""
    
    PROVIDER_PATTERNS = {
        'openrouter': [
            'openrouter.ai',
        ],
        'gemini': [
            'generativelanguage.googleapis.com',
            'googleapis.com',
        ],
        'openai': [
            'api.openai.com',
        ],
        'azure': [
            'openai.azure.com',
        ],
    }
    
    def __init__(self, base_url: str):
        """
        Initialize provider detector.
        
        Args:
            base_url: API base URL (e.g., "https://openrouter.ai/api/v1")
        """
        self.base_url = base_url
        self.provider = self._detect_provider()
    
    def _detect_provider(self) -> str:
        """
        Detect provider from base URL.
        
        Returns:
            Provider name ('openrouter', 'gemini', 'openai', 'azure', 'unknown')
        """
        try:
            parsed = urlparse(self.base_url)
            hostname = parsed.hostname or ''
            
            for provider, patterns in self.PROVIDER_PATTERNS.items():
                if any(pattern in hostname for pattern in patterns):
                    return provider
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def normalize_model_name(self, model_name: str) -> str:
        """
        Normalize model name based on detected provider.
        
        For OpenRouter: Ensures provider prefix (e.g., "google/gemini-2.0-flash")
        For Direct APIs: Strips provider prefix (e.g., "gemini-2.0-flash")
        
        Args:
            model_name: Original model name
            
        Returns:
            Normalized model name for the provider
        """
        if self.provider == 'openrouter':
            return self._normalize_for_openrouter(model_name)
        elif self.provider == 'gemini':
            return self._normalize_for_gemini(model_name)
        elif self.provider == 'openai':
            return self._normalize_for_openai(model_name)
        else:
            # Unknown provider, return as-is
            return model_name
    
    def _normalize_for_openrouter(self, model_name: str) -> str:
        """
        Normalize model name for OpenRouter.
        
        OpenRouter requires provider prefixes like:
        - google/gemini-2.0-flash-exp
        - anthropic/claude-opus-4
        - openai/gpt-4o
        
        Args:
            model_name: Original model name
            
        Returns:
            Model name with provider prefix
        """
        # If already has a provider prefix, return as-is
        if '/' in model_name:
            return model_name
        
        # Detect provider from model name and add prefix
        if model_name.startswith('gemini-'):
            return f'google/{model_name}'
        elif model_name.startswith('claude-'):
            return f'anthropic/{model_name}'
        elif model_name.startswith('gpt-') or model_name.startswith('o1-') or model_name.startswith('o3-'):
            return f'openai/{model_name}'
        elif model_name.startswith('llama-'):
            return f'meta-llama/{model_name}'
        else:
            # Unknown model, return as-is
            return model_name
    
    def _normalize_for_gemini(self, model_name: str) -> str:
        """
        Normalize model name for direct Gemini API.
        
        Gemini API expects model names without provider prefix:
        - gemini-2.0-flash-exp (not google/gemini-2.0-flash-exp)
        
        Args:
            model_name: Original model name
            
        Returns:
            Model name without provider prefix
        """
        # Strip provider prefix if present
        if '/' in model_name:
            return model_name.split('/', 1)[1]
        return model_name
    
    def _normalize_for_openai(self, model_name: str) -> str:
        """
        Normalize model name for OpenAI API.
        
        OpenAI API expects model names without provider prefix:
        - gpt-4o (not openai/gpt-4o)
        
        Args:
            model_name: Original model name
            
        Returns:
            Model name without provider prefix
        """
        # Strip provider prefix if present
        if '/' in model_name:
            return model_name.split('/', 1)[1]
        return model_name
    
    def get_provider_info(self) -> dict:
        """
        Get provider information.
        
        Returns:
            Dictionary with provider details
        """
        return {
            'provider': self.provider,
            'base_url': self.base_url,
            'requires_prefix': self.provider == 'openrouter',
        }


def detect_and_normalize(base_url: str, model_name: str) -> Tuple[str, dict]:
    """
    Convenience function to detect provider and normalize model name.
    
    Args:
        base_url: API base URL
        model_name: Original model name
        
    Returns:
        Tuple of (normalized_model_name, provider_info)
    """
    detector = ProviderDetector(base_url)
    normalized = detector.normalize_model_name(model_name)
    info = detector.get_provider_info()
    
    return normalized, info


def validate_provider_config(config) -> bool:
    """
    Validate provider configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        True if valid, False otherwise
    """
    # Basic validation logic
    if not config.openai_api_key and not config.openai_base_url:
        return False
        
    # Check for common misconfigurations
    if "anthropic" in config.openai_base_url:
        print("⚠️  Warning: Base URL looks like Anthropic API. This proxy is for OpenAI-compatible providers.")
        
    return True


validate_provider_configuration = validate_provider_config


