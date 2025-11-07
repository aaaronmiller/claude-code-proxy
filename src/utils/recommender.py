"""Intelligent model recommender based on usage patterns and correlations."""

import json
import os
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime


class ModelRecommender:
    """Analyze usage patterns and recommend better/free alternatives."""

    MODELS_DB = os.path.join(os.path.dirname(__file__), "..", "..", "models", "openrouter_models.json")
    MODES_DB = os.path.join(os.path.dirname(__file__), "..", "..", "modes.json")

    def __init__(self):
        self.models_data = self._load_models()
        self.modes_data = self._load_modes()

    def _load_models(self) -> Dict[str, Any]:
        """Load models database."""
        if os.path.exists(self.MODELS_DB):
            with open(self.MODELS_DB, 'r') as f:
                return json.load(f)
        return {}

    def _load_modes(self) -> Dict[str, Any]:
        """Load saved modes."""
        if os.path.exists(self.MODES_DB):
            with open(self.MODES_DB, 'r') as f:
                data = json.load(f)
                return data.get("modes", {})
        return {}

    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze how models are used together in modes."""
        patterns = {
            "big_models": Counter(),
            "middle_models": Counter(),
            "small_models": Counter(),
            "reasoning_usage": Counter(),
            "verbosity_usage": Counter(),
            "provider_usage": Counter(),
        }

        for mode_id, mode in self.modes_data.items():
            config = mode.get("config", {})

            # Count model usage
            big_model = config.get("BIG_MODEL", "")
            middle_model = config.get("MIDDLE_MODEL", "")
            small_model = config.get("SMALL_MODEL", "")

            if big_model:
                patterns["big_models"][big_model] += 1
            if middle_model:
                patterns["middle_models"][middle_model] += 1
            if small_model:
                patterns["small_models"][small_model] += 1

            # Count reasoning usage
            reasoning = config.get("REASONING_EFFORT", "")
            if reasoning:
                patterns["reasoning_usage"][reasoning] += 1

            # Count verbosity usage
            verbosity = config.get("VERBOSITY", "")
            if verbosity:
                patterns["verbosity_usage"][verbosity] += 1

            # Count provider usage
            for model in [big_model, middle_model, small_model]:
                if model:
                    provider = self._get_provider_from_model(model)
                    if provider:
                        patterns["provider_usage"][provider] += 1

        return patterns

    def _get_provider_from_model(self, model_id: str) -> str:
        """Extract provider from model ID."""
        if model_id.startswith("lmstudio/"):
            return "lmstudio"
        elif model_id.startswith("ollama/"):
            return "ollama"
        elif "/" in model_id:
            return model_id.split("/")[0]
        return "unknown"

    def find_model_alternatives(self, model_id: str, alternatives_type: str = "all") -> List[Dict[str, Any]]:
        """Find alternative models to a given model."""
        if not self.models_data:
            return []

        all_models = (
            self.models_data.get("local_models", []) +
            self.models_data.get("reasoning_models", []) +
            self.models_data.get("verbosity_models", []) +
            self.models_data.get("standard_models", [])
        )

        # Find the target model
        target_model = None
        for model in all_models:
            if model.get("id") == model_id:
                target_model = model
                break

        if not target_model:
            return []

        alternatives = []

        # Get target model properties
        target_source = target_model.get("source", "")
        target_reasoning = target_model.get("supports_reasoning", False)
        target_vision = target_model.get("supports_vision", False)
        target_context = target_model.get("context_length", 0)
        target_price = target_model.get("pricing", {}).get("prompt_numeric", 0.0)
        target_is_free = target_model.get("is_free", False)

        for model in all_models:
            if model.get("id") == model_id:
                continue  # Skip the same model

            score = 0
            reasons = []

            # Type-specific filtering and scoring
            if alternatives_type == "free" and not model.get("is_free", False):
                continue
            elif alternatives_type == "local" and model.get("source", "") not in ["lmstudio", "ollama"]:
                continue
            elif alternatives_type == "reasoning" and not model.get("supports_reasoning", False):
                continue
            elif alternatives_type == "vision" and not model.get("supports_vision", False):
                continue

            # Score based on features
            if model.get("supports_reasoning") == target_reasoning:
                score += 10
                if target_reasoning:
                    reasons.append("Has same reasoning support")

            if model.get("supports_vision") == target_vision:
                score += 5
                if target_vision:
                    reasons.append("Has same vision support")

            # Context length similarity
            model_context = model.get("context_length", 0)
            if target_context and model_context:
                context_diff = abs(target_context - model_context) / target_context
                if context_diff < 0.2:  # Within 20%
                    score += 10
                    reasons.append(f"Similar context length ({model_context:,} tokens)")
                elif context_diff < 0.5:  # Within 50%
                    score += 5

            # Price comparison
            model_price = model.get("pricing", {}).get("prompt_numeric", 0.0)
            if not target_is_free and not model.get("is_free", False):
                price_ratio = model_price / target_price if target_price > 0 else 0
                if price_ratio < 0.5:  # 50% cheaper or less
                    score += 15
                    reasons.append(f"Much cheaper (${model_price:.6f} vs ${target_price:.6f} per 1M tokens)")
                elif price_ratio < 0.8:  # 20% cheaper
                    score += 8
                    reasons.append(f"Cheaper (${model_price:.6f} vs ${target_price:.6f} per 1M tokens)")

            # Free alternative to paid
            if target_price > 0 and model.get("is_free", False):
                score += 20
                reasons.append("Completely free alternative")

            # Source diversity
            if model.get("source", "") != target_source:
                score += 3
                reasons.append(f"Different provider ({model.get('source', 'unknown')})")

            # Model size similarity (rough estimate from name)
            target_name = target_model.get("id", "").lower()
            model_name = model.get("id", "").lower()

            # Extract size info (e.g., "8b", "70b", "405b")
            def extract_size(name):
                import re
                match = re.search(r'(\d+)([bm])', name)
                if match:
                    num = int(match.group(1))
                    unit = match.group(2)
                    return num * 1000 if unit == 'b' else num
                return 0

            target_size = extract_size(target_name)
            model_size = extract_size(model_name)

            if target_size and model_size:
                size_diff = abs(target_size - model_size) / target_size
                if size_diff < 0.3:  # Within 30%
                    score += 7
                    reasons.append("Similar model size")

            if score > 0:
                alternatives.append({
                    "model": model,
                    "score": score,
                    "reasons": reasons
                })

        # Sort by score
        alternatives.sort(key=lambda x: x["score"], reverse=True)

        return alternatives[:10]  # Return top 10

    def find_correlated_models(self, model_id: str) -> List[Dict[str, Any]]:
        """Find models that are commonly used together with the given model."""
        correlations = defaultdict(int)

        for mode_id, mode in self.modes_data.items():
            config = mode.get("config", {})
            models_in_mode = [
                config.get("BIG_MODEL", ""),
                config.get("MIDDLE_MODEL", ""),
                config.get("SMALL_MODEL", "")
            ]

            # If our target model is in this mode, increment correlations
            if model_id in models_in_mode:
                for other_model in models_in_mode:
                    if other_model and other_model != model_id:
                        correlations[other_model] += 1

        # Sort by correlation count
        sorted_correlations = sorted(correlations.items(), key=lambda x: x[1], reverse=True)

        # Get full model info
        result = []
        for correlated_model_id, count in sorted_correlations[:5]:
            # Find the model in our database
            all_models = (
                self.models_data.get("local_models", []) +
                self.models_data.get("reasoning_models", []) +
                self.models_data.get("verbosity_models", []) +
                self.models_data.get("standard_models", [])
            )

            for model in all_models:
                if model.get("id") == correlated_model_id:
                    result.append({
                        "model": model,
                        "correlation_count": count
                    })
                    break

        return result

    def recommend_based_on_usage(self, slot: str = "big") -> List[Dict[str, Any]]:
        """Recommend models based on usage patterns."""
        patterns = self.analyze_usage_patterns()

        if slot == "big":
            most_used = patterns["big_models"].most_common(10)
        elif slot == "middle":
            most_used = patterns["middle_models"].most_common(10)
        elif slot == "small":
            most_used = patterns["small_models"].most_common(10)
        else:
            return []

        # Get full model info
        result = []
        for model_id, count in most_used:
            all_models = (
                self.models_data.get("local_models", []) +
                self.models_data.get("reasoning_models", []) +
                self.models_data.get("verbosity_models", []) +
                self.models_data.get("standard_models", [])
            )

            for model in all_models:
                if model.get("id") == model_id:
                    result.append({
                        "model": model,
                        "usage_count": count
                    })
                    break

        return result

    def get_recommendations_summary(self) -> Dict[str, Any]:
        """Get a summary of all recommendations."""
        patterns = self.analyze_usage_patterns()

        return {
            "total_modes": len(self.modes_data),
            "most_used_big_model": patterns["big_models"].most_common(1)[0] if patterns["big_models"] else None,
            "most_used_middle_model": patterns["middle_models"].most_common(1)[0] if patterns["middle_models"] else None,
            "most_used_small_model": patterns["small_models"].most_common(1)[0] if patterns["small_models"] else None,
            "preferred_reasoning": patterns["reasoning_usage"].most_common(1)[0] if patterns["reasoning_usage"] else None,
            "provider_distribution": dict(patterns["provider_usage"]),
        }

    def suggest_free_alternatives(self, paid_models: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Suggest free alternatives to a list of paid models."""
        suggestions = {}

        for model_id in paid_models:
            alternatives = self.find_model_alternatives(model_id, alternatives_type="free")
            suggestions[model_id] = alternatives[:5]  # Top 5 free alternatives

        return suggestions

    def export_recommendations(self, model_id: str, output_file: str) -> bool:
        """Export recommendations for a model to a file."""
        try:
            recommendations = {
                "model": model_id,
                "alternatives": {
                    "all": self.find_model_alternatives(model_id, "all"),
                    "free": self.find_model_alternatives(model_id, "free"),
                    "local": self.find_model_alternatives(model_id, "local"),
                    "reasoning": self.find_model_alternatives(model_id, "reasoning"),
                },
                "correlated": self.find_correlated_models(model_id),
                "usage_based": self.recommend_based_on_usage(),
            }

            with open(output_file, 'w') as f:
                json.dump(recommendations, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Error exporting recommendations: {e}")
            return False


def main():
    """Test the recommender."""
    recommender = ModelRecommender()

    print("Model Recommender - Analysis Report")
    print("=" * 70)

    # Get usage patterns
    patterns = recommender.analyze_usage_patterns()

    print(f"\nTotal saved modes: {len(recommender.modes_data)}")
    print(f"\nMost used BIG models:")
    for model, count in patterns["big_models"].most_common(5):
        print(f"  - {model}: {count} modes")

    print(f"\nPreferred reasoning effort:")
    for effort, count in patterns["reasoning_usage"].most_common(3):
        print(f"  - {effort}: {count} modes")

    # Find alternatives to a model
    if patterns["big_models"]:
        sample_model = patterns["big_models"].most_common(1)[0][0]
        print(f"\n\nFree alternatives to {sample_model}:")
        alternatives = recommender.find_model_alternatives(sample_model, "free")
        for alt in alternatives[:3]:
            print(f"  - {alt['model']['id']} (score: {alt['score']})")
            for reason in alt['reasons'][:2]:
                print(f"    • {reason}")


if __name__ == "__main__":
    main()
