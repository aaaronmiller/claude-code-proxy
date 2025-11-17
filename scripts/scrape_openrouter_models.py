#!/usr/bin/env python3
"""
Scrape OpenRouter models page and create a CSV database of model limits.

This script fetches model data from OpenRouter's API and creates a CSV file
with context limits and output limits for all available models.
"""

import asyncio
import csv
import json
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)


async def fetch_openrouter_models():
    """Fetch model data from OpenRouter API."""
    url = "https://openrouter.ai/api/v1/models"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []


def parse_model_limits(model_data):
    """
    Parse model data and extract limits.
    
    Returns:
        dict with model_id, context_limit, output_limit
    """
    model_id = model_data.get("id", "")
    
    # Get context length
    context_length = model_data.get("context_length", 0)
    
    # Get max output tokens from top_provider or pricing
    max_output = 0
    
    # Try top_provider first
    top_provider = model_data.get("top_provider", {})
    if isinstance(top_provider, dict):
        max_output = top_provider.get("max_completion_tokens", 0)
    
    # Fallback: use context_length / 2 as a reasonable default for output
    if max_output == 0 and context_length > 0:
        max_output = context_length // 2
    
    # Some models have explicit limits in architecture
    architecture = model_data.get("architecture", {})
    if isinstance(architecture, dict):
        if "max_output_tokens" in architecture:
            max_output = architecture["max_output_tokens"]
    
    return {
        "model_id": model_id,
        "context_limit": context_length,
        "output_limit": max_output,
        "name": model_data.get("name", ""),
        "description": model_data.get("description", "")[:100]  # Truncate
    }


async def main():
    """Main function to scrape and save model limits."""
    print("🔍 Fetching models from OpenRouter API...")
    
    models = await fetch_openrouter_models()
    
    if not models:
        print("❌ No models fetched. Check your internet connection.")
        return
    
    print(f"✅ Fetched {len(models)} models")
    
    # Parse model limits
    print("📊 Parsing model limits...")
    model_limits = []
    
    for model in models:
        limits = parse_model_limits(model)
        if limits["model_id"] and limits["context_limit"] > 0:
            model_limits.append(limits)
    
    print(f"✅ Parsed {len(model_limits)} models with valid limits")
    
    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Write to CSV
    csv_path = models_dir / "model_limits.csv"
    print(f"💾 Writing to {csv_path}...")
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["model_id", "context_limit", "output_limit", "name", "description"]
        )
        writer.writeheader()
        writer.writerows(model_limits)
    
    print(f"✅ Saved {len(model_limits)} models to {csv_path}")
    
    # Also save as JSON for easier programmatic access
    json_path = models_dir / "model_limits.json"
    json_data = {
        item["model_id"]: {
            "context": item["context_limit"],
            "output": item["output_limit"],
            "name": item["name"]
        }
        for item in model_limits
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    
    print(f"✅ Saved JSON to {json_path}")
    
    # Print some stats
    print("\n📈 Statistics:")
    print(f"  Total models: {len(model_limits)}")
    max_context = max((m['context_limit'] or 0) for m in model_limits)
    max_output = max((m['output_limit'] or 0) for m in model_limits)
    print(f"  Max context: {max_context:,} tokens")
    print(f"  Max output: {max_output:,} tokens")
    
    # Show some examples
    print("\n🔍 Sample models:")
    for model in sorted(model_limits, key=lambda x: x["context_limit"] or 0, reverse=True)[:5]:
        ctx = model['context_limit'] or 0
        out = model['output_limit'] or 0
        print(f"  {model['model_id']}: {ctx:,} context / {out:,} output")


if __name__ == "__main__":
    asyncio.run(main())
