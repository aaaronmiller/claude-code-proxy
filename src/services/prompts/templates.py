"""Pre-built mode templates for quick setup."""

from typing import Dict, List, Any


class ModeTemplates:
    """Pre-configured mode templates."""

    TEMPLATES = {
        "free-tier": {
            "name": "Free Tier (No API Costs)",
            "description": "Completely free models running on your local machine. Perfect for development and testing.",
            "tags": ["free", "local", "no-api-key"],
            "config": {
                "BIG_MODEL": "ollama/qwen2.5:72b",
                "MIDDLE_MODEL": "ollama/llama3.1:70b",
                "SMALL_MODEL": "ollama/llama3.1:8b",
                "REASONING_EFFORT": "medium",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "ollama_running": True,
                "models_installed": ["qwen2.5:72b", "llama3.1:70b", "llama3.1:8b"]
            }
        },

        "development": {
            "name": "Development Setup",
            "description": "Cost-effective setup for daily development. Good balance of quality and cost.",
            "tags": ["development", "balanced", "cost-effective"],
            "config": {
                "BIG_MODEL": "qwen/qwen-2.5-thinking-32b",
                "MIDDLE_MODEL": "qwen/qwen-2.5-thinking-14b",
                "SMALL_MODEL": "qwen/qwen-2.5-7b-instruct",
                "REASONING_EFFORT": "medium",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "debug",
            },
            "requirements": {
                "openrouter_api_key": True
            }
        },

        "production": {
            "name": "Production Grade",
            "description": "Premium setup with GPT-5 for maximum quality. Best for production workloads.",
            "tags": ["production", "premium", "high-quality"],
            "config": {
                "BIG_MODEL": "openai/gpt-5",
                "MIDDLE_MODEL": "openai/gpt-4o",
                "SMALL_MODEL": "gpt-4o-mini",
                "REASONING_EFFORT": "high",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "openrouter_api_key": True,
                "budget": "high"
            }
        },

        "reasoning-heavy": {
            "name": "Reasoning Intensive",
            "description": "Optimized for complex reasoning tasks. Uses high-effort reasoning models.",
            "tags": ["reasoning", "analysis", "complex-tasks"],
            "config": {
                "BIG_MODEL": "openai/o3",
                "MIDDLE_MODEL": "openai/o3-mini",
                "SMALL_MODEL": "qwen/qwen-2.5-thinking-32b",
                "REASONING_EFFORT": "high",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "openrouter_api_key": True,
                "high_token_limit": True
            }
        },

        "vision": {
            "name": "Vision & Multimodal",
            "description": "Specialized for image processing and multimodal tasks.",
            "tags": ["vision", "multimodal", "images"],
            "config": {
                "BIG_MODEL": "qwen/qwen-vl-plus",
                "MIDDLE_MODEL": "qwen/qwen-vl-max",
                "SMALL_MODEL": "qwen/qwen-vl-turbo",
                "REASONING_EFFORT": "medium",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "openrouter_api_key": True
            }
        },

        "fast-inference": {
            "name": "Fast Inference",
            "description": "Optimized for speed. Good for real-time applications and rapid iteration.",
            "tags": ["speed", "fast", "real-time"],
            "config": {
                "BIG_MODEL": "openai/gpt-4o-mini",
                "MIDDLE_MODEL": "qwen/qwen-2.5-7b-instruct",
                "SMALL_MODEL": "qwen/qwen-2.5-3b-instruct",
                "REASONING_EFFORT": "low",
                "VERBOSITY": "default",
                "REASONING_EXCLUDE": "true",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "warning",
            },
            "requirements": {
                "openrouter_api_key": True
            }
        },

        "local-reasoning": {
            "name": "Local Reasoning (Free)",
            "description": "Free local models with reasoning support. No API costs!",
            "tags": ["free", "local", "reasoning", "no-api-key"],
            "config": {
                "BIG_MODEL": "ollama/deepseek-v2.5:236b",
                "MIDDLE_MODEL": "ollama/qwen2.5:72b",
                "SMALL_MODEL": "ollama/qwen2.5:32b",
                "REASONING_EFFORT": "high",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "ollama_running": True,
                "models_installed": ["deepseek-v2.5:236b", "qwen2.5:72b", "qwen2.5:32b"]
            }
        },

        "budget": {
            "name": "Budget Conscious",
            "description": "Ultra-low cost models for experimentation and learning.",
            "tags": ["budget", "cheap", "experiments"],
            "config": {
                "BIG_MODEL": "deepseek/deepseek-chat",
                "MIDDLE_MODEL": "qwen/qwen-2.5-plus",
                "SMALL_MODEL": "meta-llama/llama-3.2-3b-instruct",
                "REASONING_EFFORT": "low",
                "VERBOSITY": "default",
                "REASONING_EXCLUDE": "true",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "openrouter_api_key": True
            }
        },

        "lmstudio-setup": {
            "name": "LMStudio (Local GUI)",
            "description": "Set up for LMStudio with its native models. Full control via GUI.",
            "tags": ["local", "lmstudio", "gui", "no-api-key"],
            "config": {
                "BIG_MODEL": "lmstudio/Meta-Llama-3.1-405B-Instruct",
                "MIDDLE_MODEL": "lmstudio/Meta-Llama-3.1-70B-Instruct",
                "SMALL_MODEL": "lmstudio/Meta-Llama-3.1-8B-Instruct",
                "REASONING_EFFORT": "medium",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "lmstudio_running": True,
                "models_loaded": True
            }
        },

        "research": {
            "name": "Research & Analysis",
            "description": "High-context models for deep analysis and research tasks.",
            "tags": ["research", "analysis", "deep-context"],
            "config": {
                "BIG_MODEL": "amazon/nova-premier-v1",
                "MIDDLE_MODEL": "qwen/qwen-2.5-plus-0728",
                "SMALL_MODEL": "google/gemini-2.0-flash-exp",
                "REASONING_EFFORT": "high",
                "VERBOSITY": "high",
                "REASONING_EXCLUDE": "false",
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "LOG_LEVEL": "info",
            },
            "requirements": {
                "openrouter_api_key": True,
                "high_context": True
            }
        }
    }

    @classmethod
    def get_template_names(cls) -> List[str]:
        """Get list of all template names."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template(cls, name: str) -> Dict[str, Any]:
        """Get a specific template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """Get list of all templates with metadata."""
        return [
            {
                "name": name,
                "display_name": data["name"],
                "description": data["description"],
                "tags": data["tags"]
            }
            for name, data in cls.TEMPLATES.items()
        ]

    @classmethod
    def get_config(cls, name: str) -> Dict[str, str]:
        """Get the configuration for a template."""
        template = cls.TEMPLATES.get(name)
        if template:
            return template["config"]
        return None

    @classmethod
    def get_requirements(cls, name: str) -> Dict[str, Any]:
        """Get the requirements for a template."""
        template = cls.TEMPLATES.get(name)
        if template:
            return template.get("requirements", {})
        return {}


# Wrapper functions for backward compatibility and ease of use

def get_available_templates() -> List[str]:
    """Get list of available template names."""
    return ModeTemplates.get_template_names()

def get_template(name: str) -> Dict[str, Any]:
    """Get template details by name."""
    return ModeTemplates.get_template(name)

def apply_template(name: str) -> Dict[str, str]:
    """
    Get configuration for a template.
    Returns the config dict if found, None otherwise.
    """
    return ModeTemplates.get_config(name)

