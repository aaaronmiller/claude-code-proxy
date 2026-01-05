#!/usr/bin/env python3
"""
OpenRouter Model Enricher

Parses the OpenRouter API response and extracts all useful model metadata
into a structured JSON format for use in TUI and Web UI model selectors.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


def parse_models_file(filepath: str) -> List[Dict[str, Any]]:
    """Parse the OpenRouter models API response."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unexpected models file format")


def extract_provider(model_id: str) -> str:
    """Extract provider name from model ID."""
    if '/' in model_id:
        return model_id.split('/')[0]
    return "unknown"


def supports_feature(params: List[str], feature: str) -> bool:
    """Check if model supports a specific feature."""
    return feature in params if params else False


def enrich_model(model: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw OpenRouter model data into enriched format.
    
    Extracts all useful fields for display in model selectors.
    """
    model_id = model.get('id', '')
    architecture = model.get('architecture', {})
    pricing = model.get('pricing', {})
    top_provider = model.get('top_provider', {})
    supported_params = model.get('supported_parameters', [])
    
    # Parse pricing (convert string to float, per million tokens)
    def parse_price(price_str: str) -> float:
        try:
            return float(price_str) * 1_000_000 if price_str else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    input_price = parse_price(pricing.get('prompt', '0'))
    output_price = parse_price(pricing.get('completion', '0'))
    
    # Determine capabilities
    input_modalities = architecture.get('input_modalities', ['text'])
    output_modalities = architecture.get('output_modalities', ['text'])
    
    supports_vision = any(m in input_modalities for m in ['image', 'video'])
    supports_audio = 'audio' in input_modalities
    supports_files = 'file' in input_modalities
    supports_reasoning = supports_feature(supported_params, 'reasoning') or supports_feature(supported_params, 'include_reasoning')
    supports_tools = supports_feature(supported_params, 'tools')
    supports_structured = supports_feature(supported_params, 'structured_outputs')
    
    # Determine if free
    is_free = (input_price == 0 and output_price == 0) or model_id.endswith(':free')
    
    return {
        # Identity
        "id": model_id,
        "name": model.get('name', model_id),
        "provider": extract_provider(model_id),
        "canonical_slug": model.get('canonical_slug', ''),
        "hugging_face_id": model.get('hugging_face_id', ''),
        
        # Description
        "description": model.get('description', ''),
        
        # Context & Limits
        "context_length": model.get('context_length', 0),
        "max_completion_tokens": top_provider.get('max_completion_tokens', 0) or 0,
        
        # Architecture
        "modality": architecture.get('modality', 'text->text'),
        "input_modalities": input_modalities,
        "output_modalities": output_modalities,
        "tokenizer": architecture.get('tokenizer', 'Unknown'),
        
        # Capabilities
        "supports_reasoning": supports_reasoning,
        "supports_tools": supports_tools,
        "supports_vision": supports_vision,
        "supports_audio": supports_audio,
        "supports_files": supports_files,
        "supports_structured_output": supports_structured,
        
        # Pricing (per million tokens)
        "pricing": {
            "input_per_million": round(input_price, 4),
            "output_per_million": round(output_price, 4),
            "is_free": is_free
        },
        
        # Moderation
        "is_moderated": top_provider.get('is_moderated', False),
        
        # Supported Parameters (for advanced users)
        "supported_parameters": supported_params,
        
        # Metadata
        "created": model.get('created', 0),
    }


def enrich_all_models(input_file: str, output_file: str) -> Dict[str, Any]:
    """
    Process all models and output enriched JSON.
    
    Returns summary statistics.
    """
    print(f"📖 Reading models from: {input_file}")
    models = parse_models_file(input_file)
    print(f"   Found {len(models)} models")
    
    enriched = []
    stats = {
        "total": len(models),
        "free": 0,
        "reasoning": 0,
        "vision": 0,
        "tools": 0,
        "by_provider": {}
    }
    
    for model in models:
        enriched_model = enrich_model(model)
        enriched.append(enriched_model)
        
        # Update stats
        provider = enriched_model['provider']
        stats['by_provider'][provider] = stats['by_provider'].get(provider, 0) + 1
        
        if enriched_model['pricing']['is_free']:
            stats['free'] += 1
        if enriched_model['supports_reasoning']:
            stats['reasoning'] += 1
        if enriched_model['supports_vision']:
            stats['vision'] += 1
        if enriched_model['supports_tools']:
            stats['tools'] += 1
    
    # Sort by provider, then by name
    enriched.sort(key=lambda m: (m['provider'], m['name']))
    
    # Create output structure
    output = {
        "generated_at": datetime.now().isoformat(),
        "source": "OpenRouter API",
        "stats": stats,
        "models": enriched
    }
    
    # Write output
    print(f"💾 Writing enriched data to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Enrichment complete!")
    print(f"   Total models: {stats['total']}")
    print(f"   Free models: {stats['free']}")
    print(f"   Reasoning-capable: {stats['reasoning']}")
    print(f"   Vision-capable: {stats['vision']}")
    print(f"   Tool-use capable: {stats['tools']}")
    print(f"   Providers: {len(stats['by_provider'])}")
    
    return stats


def main():
    """Main entry point."""
    # Determine paths
    project_root = Path(__file__).parent.parent.parent.parent
    input_file = project_root / "models.txt"
    output_file = project_root / "data" / "openrouter_models_enriched.json"
    
    # Check input exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("   Run: curl https://openrouter.ai/api/v1/models > models.txt")
        return
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Run enrichment
    enrich_all_models(str(input_file), str(output_file))


if __name__ == "__main__":
    main()
