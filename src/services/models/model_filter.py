"""Smart model filtering for OpenRouter and other providers."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set
from pathlib import Path


class ModelFilter:
    """Filter and prioritize models based on usage, popularity, and cost."""
    
    # Top models that are consistently popular and useful
    TOP_MODELS = [
        "google/gemini-2.0-flash-exp",
        "google/gemini-2.0-flash-thinking-exp",
        "google/gemini-1.5-pro",
        "google/gemini-1.5-flash",
        "anthropic/claude-opus-4",
        "anthropic/claude-sonnet-4",
        "anthropic/claude-3.7-sonnet",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/o1",
        "openai/o1-mini",
        "meta-llama/llama-3.3-70b-instruct",
        "meta-llama/llama-3.1-405b-instruct",
        "deepseek/deepseek-chat",
        "qwen/qwen-2.5-72b-instruct",
        "mistralai/mistral-large",
        "x-ai/grok-2",
        "perplexity/llama-3.1-sonar-large",
        "cohere/command-r-plus",
    ]
    
    # Free models that are actually good
    FREE_MODELS = [
        "google/gemini-2.0-flash-exp",
        "google/gemini-1.5-flash",
        "meta-llama/llama-3.3-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
        "qwen/qwen-2.5-72b-instruct",
        "mistralai/mistral-7b-instruct",
        "microsoft/phi-3-medium-128k-instruct",
    ]
    
    # New models (last 2 months)
    NEW_MODELS = [
        "google/gemini-2.0-flash-exp",
        "google/gemini-2.0-flash-thinking-exp",
        "anthropic/claude-3.7-sonnet",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-72b-instruct",
        "x-ai/grok-2",
        "deepseek/deepseek-chat",
    ]
    
    def __init__(self, usage_file: str = "data/model_usage.json"):
        """
        Initialize model filter.
        
        Args:
            usage_file: Path to file tracking model usage
        """
        self.usage_file = Path(usage_file)
        self.usage_data = self._load_usage_data()
    
    def _load_usage_data(self) -> Dict:
        """Load model usage data from file."""
        if not self.usage_file.exists():
            return {"models": {}, "last_updated": None}
        
        try:
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {"models": {}, "last_updated": None}
    
    def _save_usage_data(self):
        """Save model usage data to file."""
        try:
            self.usage_data["last_updated"] = datetime.now().isoformat()
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception:
            pass
    
    def track_model_usage(self, model_name: str):
        """
        Track that a model was used.
        
        Args:
            model_name: Name of the model that was used
        """
        models = self.usage_data.get("models", {})
        
        if model_name not in models:
            models[model_name] = {
                "count": 0,
                "last_used": None,
                "first_used": datetime.now().isoformat()
            }
        
        models[model_name]["count"] += 1
        models[model_name]["last_used"] = datetime.now().isoformat()
        
        self.usage_data["models"] = models
        self._save_usage_data()
    
    def get_recently_used_models(self, limit: int = 20) -> List[str]:
        """
        Get most recently used models.
        
        Args:
            limit: Maximum number of models to return
            
        Returns:
            List of model names sorted by most recent usage
        """
        models = self.usage_data.get("models", {})
        
        # Sort by last_used timestamp
        sorted_models = sorted(
            models.items(),
            key=lambda x: x[1].get("last_used", ""),
            reverse=True
        )
        
        return [model for model, _ in sorted_models[:limit]]
    
    def get_most_used_models(self, limit: int = 20) -> List[str]:
        """
        Get most frequently used models.
        
        Args:
            limit: Maximum number of models to return
            
        Returns:
            List of model names sorted by usage count
        """
        models = self.usage_data.get("models", {})
        
        # Sort by count
        sorted_models = sorted(
            models.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True
        )
        
        return [model for model, _ in sorted_models[:limit]]

    def get_filtered_models(
        self,
        all_models: List[str],
        include_free: bool = True,
        include_top: bool = True,
        include_recent: bool = True,
        max_total: int = 100
    ) -> List[str]:
        """
        Get filtered list of models with Smart Sorting.
        
        Sorting Order:
        1. New & Free (The "Stealth" free models)
        2. Recently Used (Your favorites)
        3. Top Free (The best always-free ones)
        4. Top Paid (High quality paid)
        5. Others
        """
        unique_models = set()
        
        # 1. New Models (Prioritize New & Free)
        new_models = []
        for model in self.NEW_MODELS:
            if model in all_models:
                new_models.append(model)
                unique_models.add(model)
        
        # 2. Recently Used
        recent_models = []
        if include_recent:
            usage_list = self.get_recently_used_models(limit=10)
            for model in usage_list:
                if model in all_models and model not in unique_models:
                    recent_models.append(model)
                    unique_models.add(model)
                    
        # 3. Top Free (excluding already added)
        free_models = []
        if include_free:
            for model in self.FREE_MODELS:
                if model in all_models and model not in unique_models:
                    free_models.append(model)
                    unique_models.add(model)
                    
        # 4. Top Paid/Popular
        top_models = []
        if include_top:
            for model in self.TOP_MODELS:
                if model in all_models and model not in unique_models:
                    top_models.append(model)
                    unique_models.add(model)
                    
        # 5. Fill the rest from all_models until max_total
        # Only if we need more padding
        rest_models = []
        if len(unique_models) < max_total:
            for model in all_models:
                if model not in unique_models:
                    rest_models.append(model)
                    unique_models.add(model)
                    if len(unique_models) >= max_total:
                        break
                        
        # Combine lists in priority order
        # Note: We return a flat list, but the UI can use is_new_model() etc to show badges
        return new_models + recent_models + free_models + top_models + rest_models

    def is_new_model(self, model_name: str) -> bool:
        """Check if model is considered 'new'."""
        return model_name in self.NEW_MODELS
    
    def is_free_model(self, model_name: str) -> bool:
        """
        Check if a model is free.
        
        Args:
            model_name: Model name to check
            
        Returns:
            True if model is free
        """
        return model_name in self.FREE_MODELS
    
    def is_top_model(self, model_name: str) -> bool:
        """
        Check if a model is in the top models list.
        
        Args:
            model_name: Model name to check
            
        Returns:
            True if model is a top model
        """
        return model_name in self.TOP_MODELS


# Global instance
model_filter = ModelFilter()

def filter_models(all_models: List[str], **kwargs) -> List[str]:
    """Wrapper for model_filter.get_filtered_models"""
    return model_filter.get_filtered_models(all_models, **kwargs)

def get_available_models() -> List[str]:
    """
    Get all available models from OpenRouter/Providers.
    This is a placeholder that should ideally call the client.
    For now, returning the known top/free lists combined.
    """
    # This seems to be missing from the original file or moved.
    # Re-implementing a basic version based on known lists.
    return list(set(ModelFilter.TOP_MODELS + ModelFilter.FREE_MODELS))
