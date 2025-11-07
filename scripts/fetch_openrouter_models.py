#!/usr/bin/env python3
"""
Fetch and categorize models from multiple sources.
Identifies models supporting reasoning, verbosity, and other advanced parameters.
Extracts detailed metadata: pricing, context window, cache pricing, output limits.
"""

import json
import csv
import sys
import os
from typing import Dict, List, Any
import requests
from datetime import datetime


class MultiSourceModelFetcher:
    """Fetch and analyze models from multiple sources."""

    OPENROUTER_API = "https://openrouter.ai/api/v1/models"
    LMSTUDIO_DEFAULT_HOST = "127.0.0.1"
    LMSTUDIO_DEFAULT_PORT = 1234
    OLLAMA_DEFAULT_HOST = "127.0.0.1"
    OLLAMA_DEFAULT_PORT = 11434

    def __init__(self):
        self.all_models = []
        self.reasoning_models = []
        self.verbosity_models = []
        self.standard_models = []
        self.local_models = []

    def get_local_providers(self) -> List[Dict[str, Any]]:
        """Get common local provider configurations."""
        return [
            # LMStudio Models (at the top)
            {
                "id": "lmstudio/Meta-Llama-3.1-8B-Instruct",
                "name": "Llama 3.1 8B Instruct (LMStudio)",
                "description": "Meta Llama 3.1 8B Instruct model via LMStudio",
                "source": "lmstudio",
                "endpoint": f"http://{self.LMSTUDIO_DEFAULT_HOST}:{self.LMSTUDIO_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "lmstudio", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "lmstudio/Meta-Llama-3.1-70B-Instruct",
                "name": "Llama 3.1 70B Instruct (LMStudio)",
                "description": "Meta Llama 3.1 70B Instruct model via LMStudio",
                "source": "lmstudio",
                "endpoint": f"http://{self.LMSTUDIO_DEFAULT_HOST}:{self.LMSTUDIO_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "lmstudio", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "lmstudio/Meta-Llama-3.1-405B-Instruct",
                "name": "Llama 3.1 405B Instruct (LMStudio)",
                "description": "Meta Llama 3.1 405B Instruct model via LMStudio",
                "source": "lmstudio",
                "endpoint": f"http://{self.LMSTUDIO_DEFAULT_HOST}:{self.LMSTUDIO_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "lmstudio", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "lmstudio/Qwen2.5-72B-Instruct",
                "name": "Qwen 2.5 72B Instruct (LMStudio)",
                "description": "Qwen 2.5 72B Instruct model via LMStudio",
                "source": "lmstudio",
                "endpoint": f"http://{self.LMSTUDIO_DEFAULT_HOST}:{self.LMSTUDIO_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": True,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "lmstudio", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "lmstudio/gemma2-27b-it",
                "name": "Gemma 2 27B Instruct (LMStudio)",
                "description": "Google Gemma 2 27B Instruct model via LMStudio",
                "source": "lmstudio",
                "endpoint": f"http://{self.LMSTUDIO_DEFAULT_HOST}:{self.LMSTUDIO_DEFAULT_PORT}/v1",
                "context_length": 8192,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "lmstudio", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            # Ollama Models (also near the top)
            {
                "id": "ollama/llama3.1:8b",
                "name": "Llama 3.1 8B (Ollama)",
                "description": "Meta Llama 3.1 8B via Ollama",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "ollama/llama3.1:70b",
                "name": "Llama 3.1 70B (Ollama)",
                "description": "Meta Llama 3.1 70B via Ollama",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "ollama/llama3.1:405b",
                "name": "Llama 3.1 405B (Ollama)",
                "description": "Meta Llama 3.1 405B via Ollama",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "ollama/qwen2.5:72b",
                "name": "Qwen 2.5 72B (Ollama)",
                "description": "Qwen 2.5 72B via Ollama with thinking support",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": True,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "ollama/deepseek-v2.5:236b",
                "name": "DeepSeek V2.5 236B (Ollama)",
                "description": "DeepSeek V2.5 236B via Ollama with reasoning",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": True,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "ollama/mistral-nemo:12b",
                "name": "Mistral Nemo 12B (Ollama)",
                "description": "Mistral Nemo 12B via Ollama",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 131072,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
            {
                "id": "ollama/gemma2:27b",
                "name": "Gemma 2 27B (Ollama)",
                "description": "Google Gemma 2 27B via Ollama",
                "source": "ollama",
                "endpoint": f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1",
                "context_length": 8192,
                "supports_reasoning": False,
                "supports_verbosity": False,
                "supports_tools": True,
                "supports_vision": False,
                "is_free": True,
                "pricing": {"prompt": "$0.000000", "completion": "$0.000000"},
                "top_provider": {"name": "ollama", "weighted_capacity": 100},
                "architecture_modality": "text",
                "per_request_limits": None,
            },
        ]

    def fetch_openrouter_models(self) -> List[Dict[str, Any]]:
        """Fetch all models from OpenRouter API."""
        try:
            print("Fetching models from OpenRouter...")
            response = requests.get(self.OPENROUTER_API, timeout=30)
            response.raise_for_status()
            data = response.json()

            models = data.get("data", [])
            print(f"✓ Fetched {len(models)} models from OpenRouter")
            return models

        except requests.RequestException as e:
            print(f"✗ Error fetching models: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            sys.exit(1)

    def extract_detailed_metadata(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed metadata from model object."""
        # Extract pricing information
        pricing = model.get("pricing", {})
        prompt_price = pricing.get("prompt", "0")
        completion_price = pricing.get("completion", "0")
        cache_write_price = pricing.get("cache_write", "0")
        cache_read_price = pricing.get("cache_read", "0")

        # Clean up prices (remove $ and convert)
        def clean_price(price_str):
            if not price_str:
                return 0.0
            try:
                return float(price_str.replace("$", ""))
            except:
                return 0.0

        # Extract context and limits
        context_length = model.get("context_length")
        per_request_limits = model.get("per_request_limits")

        # Extract architecture info
        architecture = model.get("architecture", {})
        modality = architecture.get("modality", "text")

        return {
            "id": model.get("id", "unknown"),
            "name": model.get("name", "Unknown"),
            "description": model.get("description", ""),
            "source": "openrouter",
            "endpoint": "https://openrouter.ai/api/v1",
            "context_length": context_length,
            "architecture_modality": modality,
            "per_request_limits": per_request_limits,
            "pricing": {
                "prompt": prompt_price,
                "completion": completion_price,
                "cache_write": cache_write_price,
                "cache_read": cache_read_price,
                "prompt_numeric": clean_price(prompt_price),
                "completion_numeric": clean_price(completion_price),
                "cache_write_numeric": clean_price(cache_write_price),
                "cache_read_numeric": clean_price(cache_read_price),
            },
            "top_provider": model.get("top_provider", {}),
            "created": model.get("created"),
        }

    def analyze_model_capabilities(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single model's capabilities."""
        # First extract metadata
        capabilities = self.extract_detailed_metadata(model)

        # Then analyze capabilities
        model_id = capabilities["id"].lower()
        name = capabilities["name"].lower()
        description = capabilities["description"].lower()

        # Check for reasoning support
        reasoning_keywords = [
            "reasoning", "thinking", "o3", "gpt-5", "deep research",
            "qwen3", "qwen-2.5-thinking", "deepseek v3", "claude haiku"
        ]

        if any(keyword.lower() in model_id for keyword in reasoning_keywords):
            capabilities["supports_reasoning"] = True
        elif any(keyword.lower() in name for keyword in reasoning_keywords):
            capabilities["supports_reasoning"] = True
        elif any(keyword.lower() in description for keyword in reasoning_keywords):
            capabilities["supports_reasoning"] = True
        else:
            capabilities["supports_reasoning"] = False

        # Check for verbosity support
        verbosity_keywords = ["verbosity", "verbose", "detailed"]
        capabilities["supports_verbosity"] = any(
            keyword.lower() in model_id or keyword.lower() in description
            for keyword in verbosity_keywords
        )

        # Check for tool support
        capabilities["supports_tools"] = (
            model.get("tools") is not None or
            "tool" in model_id or
            "function" in model_id
        )

        # Check for vision/multimodal
        vision_keywords = ["vision", "multimodal", "image", "gpt-5", "gemini", "qwen-vl"]
        capabilities["supports_vision"] = (
            capabilities["architecture_modality"] in ["image->text", "text->image"] or
            any(keyword.lower() in model_id for keyword in vision_keywords) or
            any(keyword.lower() in description for keyword in vision_keywords)
        )

        # Check if free
        prompt_price = capabilities["pricing"]["prompt_numeric"]
        capabilities["is_free"] = prompt_price == 0.0

        return capabilities

    def categorize_models(self, models: List[Dict[str, Any]]) -> None:
        """Categorize models based on capabilities."""
        for model in models:
            capabilities = self.analyze_model_capabilities(model)

            if capabilities["supports_reasoning"]:
                self.reasoning_models.append(capabilities)
            elif capabilities["supports_verbosity"]:
                self.verbosity_models.append(capabilities)
            else:
                self.standard_models.append(capabilities)

        print(f"✓ Categorized models:")
        print(f"  - {len(self.reasoning_models)} with reasoning support")
        print(f"  - {len(self.verbosity_models)} with verbosity support")
        print(f"  - {len(self.standard_models)} standard models")

    def sort_models(self, models: List[Dict[str, Any]], sort_key: str = "id") -> List[Dict[str, Any]]:
        """Sort models by a specific key."""
        return sorted(models, key=lambda x: x.get(sort_key, "").lower())

    def get_endpoint_for_model(self, model: Dict[str, Any]) -> str:
        """Get the appropriate endpoint for a model based on its source."""
        source = model.get("source", "openrouter")

        if source == "lmstudio":
            return model.get("endpoint", f"http://{self.LMSTUDIO_DEFAULT_HOST}:{self.LMSTUDIO_DEFAULT_PORT}/v1")
        elif source == "ollama":
            return model.get("endpoint", f"http://{self.OLLAMA_DEFAULT_HOST}:{self.OLLAMA_DEFAULT_PORT}/v1")
        else:  # openrouter
            return "https://openrouter.ai/api/v1"

    def display_detailed_model_info(self, model: Dict[str, Any]) -> str:
        """Create a detailed info string for a model."""
        info_parts = [
            f"Source: {model.get('source', 'unknown')}",
            f"Endpoint: {self.get_endpoint_for_model(model)}",
        ]

        if model.get('context_length'):
            info_parts.append(f"Context: {model['context_length']:,} tokens")

        if model.get('pricing'):
            pricing = model['pricing']
            if pricing.get('prompt_numeric', 0) > 0:
                info_parts.append(f"Price: ${pricing['prompt']}/1M prompt, ${pricing['completion']}/1M completion")
            else:
                info_parts.append("Price: Free")

        if model.get('architecture_modality') and model['architecture_modality'] != 'text':
            info_parts.append(f"Modality: {model['architecture_modality']}")

        return " | ".join(info_parts)

    def save_json(self, filename: str) -> None:
        """Save all models to JSON with comprehensive metadata."""
        # Combine all models
        all_models = self.local_models + self.reasoning_models + self.verbosity_models + self.standard_models

        output = {
            "local_models": self.sort_models(self.local_models),
            "reasoning_models": self.sort_models(self.reasoning_models),
            "verbosity_models": self.sort_models(self.verbosity_models),
            "standard_models": self.sort_models(self.standard_models),
            "summary": {
                "total": len(all_models),
                "local_count": len(self.local_models),
                "reasoning_count": len(self.reasoning_models),
                "verbosity_count": len(self.verbosity_models),
                "standard_count": len(self.standard_models),
                "free_count": sum(1 for m in all_models if m.get('is_free', False)),
                "with_pricing": sum(1 for m in all_models if m.get('pricing', {}).get('prompt_numeric', 0) > 0),
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {filename}")

    def save_csv(self, filename: str) -> None:
        """Save all models to CSV with expanded fields."""
        fieldnames = [
            "id", "name", "source", "endpoint", "description",
            "supports_reasoning", "supports_verbosity", "supports_tools", "supports_vision",
            "is_free", "context_length", "architecture_modality",
            "pricing_prompt", "pricing_completion", "pricing_cache_write", "pricing_cache_read",
            "pricing_prompt_numeric", "pricing_completion_numeric"
        ]

        all_models = (
            self.local_models + self.reasoning_models + self.verbosity_models + self.standard_models
        )

        # Filter out fields not in fieldnames
        filtered_models = []
        for model in all_models:
            filtered = {k: v for k, v in model.items() if k in fieldnames}

            # Flatten pricing
            if 'pricing' in model:
                pricing = model['pricing']
                filtered['pricing_prompt'] = pricing.get('prompt', '0')
                filtered['pricing_completion'] = pricing.get('completion', '0')
                filtered['pricing_cache_write'] = pricing.get('cache_write', '0')
                filtered['pricing_cache_read'] = pricing.get('cache_read', '0')
                filtered['pricing_prompt_numeric'] = pricing.get('prompt_numeric', 0.0)
                filtered['pricing_completion_numeric'] = pricing.get('completion_numeric', 0.0)

            filtered_models.append(filtered)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_models)
        print(f"✓ Saved to {filename}")

    def display_top_models(self, category: str, models: List[Dict[str, Any]], count: int = 10) -> None:
        """Display top N models in a category with detailed info."""
        print(f"\n=== Top {count} {category.title()} Models ===")
        for i, model in enumerate(models[:count], 1):
            print(f"{i}. {model['id']}")
            print(f"   Name: {model['name']}")
            print(f"   Source: {model.get('source', 'unknown')}")
            print(f"   Reasoning: {'✓' if model['supports_reasoning'] else '✗'}")
            print(f"   Vision: {'✓' if model['supports_vision'] else '✗'}")
            print(f"   Free: {'✓' if model['is_free'] else '✗'}")
            if model['context_length']:
                print(f"   Context: {model['context_length']:,} tokens")

            # Show pricing if available
            if model.get('pricing'):
                pricing = model['pricing']
                if pricing.get('prompt_numeric', 0) > 0:
                    print(f"   Price: ${pricing['prompt']}/1M prompt, ${pricing['completion']}/1M completion")
                else:
                    print(f"   Price: Free")

            print()


def main():
    fetcher = MultiSourceModelFetcher()

    # Get local providers (LMStudio, Ollama) - put at the top
    print("Loading local provider models...")
    local_models = fetcher.get_local_providers()
    fetcher.local_models = local_models
    print(f"✓ Loaded {len(local_models)} local models (LMStudio, Ollama)")

    # Fetch OpenRouter models
    openrouter_models = fetcher.fetch_openrouter_models()

    # Categorize OpenRouter models
    fetcher.categorize_models(openrouter_models)

    # Save outputs
    output_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(output_dir, "..", "models")

    os.makedirs(models_dir, exist_ok=True)

    json_file = os.path.join(models_dir, "openrouter_models.json")
    csv_file = os.path.join(models_dir, "openrouter_models.csv")

    fetcher.save_json(json_file)
    fetcher.save_csv(csv_file)

    # Display top models
    print("\n" + "="*70)
    print("FEATURED MODELS (Local providers first)")
    print("="*70)

    fetcher.display_top_models("local", fetcher.local_models, 10)
    fetcher.display_top_models("reasoning", fetcher.reasoning_models, 10)
    fetcher.display_top_models("verbosity", fetcher.verbosity_models, 5)

    print("\n" + "="*70)
    print("Complete! Run select_model.py to configure your models.")
    print("="*70)
    print("\nLocal Providers Configured:")
    print(f"  • LMStudio: http://{fetcher.LMSTUDIO_DEFAULT_HOST}:{fetcher.LMSTUDIO_DEFAULT_PORT}/v1")
    print(f"  • Ollama: http://{fetcher.OLLAMA_DEFAULT_HOST}:{fetcher.OLLAMA_DEFAULT_PORT}/v1")


if __name__ == "__main__":
    main()
