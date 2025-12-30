"""
OpenRouter Rankings Scraper

Scrapes OpenRouter's official rankings page to get:
- Overall leaderboard (token usage)
- Programming language rankings
- Tool call rankings

Uses this data to filter "top" models for the model selector.

Usage:
    python -m src.services.models.openrouter_rankings --scrape
    python -m src.services.models.openrouter_rankings --show
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Database path
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
RANKINGS_DB_PATH = MODELS_DIR / "openrouter_rankings.json"


@dataclass
class RankedModel:
    """A model from OpenRouter rankings."""
    model_id: str
    rank: int
    category: str  # "overall", "programming", "tool_calls"
    metric_value: float = 0.0  # Usage %, score, etc.
    is_free: bool = False
    scraped_at: str = ""


class OpenRouterRankings:
    """OpenRouter rankings database."""
    
    def __init__(self):
        self._data: Dict[str, List[Dict]] = {
            "overall": [],
            "programming": [],
            "tool_calls": [],
            "updated_at": ""
        }
        self._load()
    
    def _load(self):
        """Load rankings from file."""
        if RANKINGS_DB_PATH.exists():
            try:
                with open(RANKINGS_DB_PATH, 'r') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded rankings from {RANKINGS_DB_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load rankings: {e}")
    
    def save(self):
        """Save rankings to file."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self._data["updated_at"] = datetime.now().isoformat()
        with open(RANKINGS_DB_PATH, 'w') as f:
            json.dump(self._data, f, indent=2)
        logger.info(f"Saved rankings to {RANKINGS_DB_PATH}")
    
    def set_rankings(self, category: str, models: List[RankedModel]):
        """Set rankings for a category."""
        self._data[category] = [asdict(m) for m in models]
    
    def get_top_models(self, category: str = "overall", n: int = 20) -> List[str]:
        """Get top N model IDs for a category."""
        rankings = self._data.get(category, [])
        return [r["model_id"] for r in rankings[:n]]
    
    def is_top_model(self, model_id: str, categories: List[str] = None) -> bool:
        """Check if model is in top rankings."""
        if categories is None:
            categories = ["overall", "programming", "tool_calls"]
        
        for cat in categories:
            if model_id in self.get_top_models(cat, 30):
                return True
        return False
    
    def get_model_rank(self, model_id: str, category: str = "overall") -> Optional[int]:
        """Get rank for a specific model."""
        rankings = self._data.get(category, [])
        for r in rankings:
            if r["model_id"] == model_id:
                return r["rank"]
        return None


async def scrape_rankings_with_playwright() -> Dict[str, List[RankedModel]]:
    """
    Scrape OpenRouter rankings page using Playwright.
    
    Returns rankings for overall, programming, and tool_calls categories.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install")
        return {}
    
    results = {
        "overall": [],
        "programming": [],
        "tool_calls": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("🔄 Navigating to OpenRouter rankings...")
            await page.goto("https://openrouter.ai/rankings", wait_until="networkidle")
            await asyncio.sleep(3)  # Let charts load
            
            # Try to extract from page content
            # The page uses charts/tables that may have model names
            content = await page.content()
            text = await page.inner_text("body")
            
            # Look for model patterns in the text
            import re
            
            # Find model IDs (pattern: provider/model-name)
            model_pattern = r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+(?::[a-zA-Z0-9_-]+)?)'
            found_models = re.findall(model_pattern, text)
            
            # Filter to likely model IDs (exclude obvious non-models)
            excluded_prefixes = ['http', 'www', 'openrouter', 'api', 'docs']
            valid_models = []
            for m in found_models:
                if not any(m.lower().startswith(ex) for ex in excluded_prefixes):
                    if m not in valid_models:
                        valid_models.append(m)
            
            print(f"📊 Found {len(valid_models)} model references")
            
            # Try clicking on different tabs/sections
            sections = [
                ("#market-share", "overall"),
                ("#programming-languages", "programming"),
                ("#tools", "tool_calls"),
            ]
            
            for selector, category in sections:
                try:
                    # Try to navigate to section
                    await page.goto(f"https://openrouter.ai/rankings{selector}", wait_until="networkidle")
                    await asyncio.sleep(2)
                    
                    section_text = await page.inner_text("body")
                    section_models = re.findall(model_pattern, section_text)
                    
                    rank = 1
                    seen = set()
                    for m in section_models:
                        if m not in seen and not any(m.lower().startswith(ex) for ex in excluded_prefixes):
                            seen.add(m)
                            results[category].append(RankedModel(
                                model_id=m,
                                rank=rank,
                                category=category,
                                is_free=":free" in m.lower(),
                                scraped_at=datetime.now().isoformat()
                            ))
                            rank += 1
                            if rank > 30:
                                break
                    
                    print(f"   {category}: {len(results[category])} models")
                    
                except Exception as e:
                    logger.debug(f"Error scraping {category}: {e}")
            
            # If we didn't get much data, use known top models as fallback
            if len(results["overall"]) < 5:
                print("⚠️  Limited data from scraping, using known top models...")
                results = _get_fallback_rankings()
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            results = _get_fallback_rankings()
        finally:
            await browser.close()
    
    return results


def _get_fallback_rankings() -> Dict[str, List[RankedModel]]:
    """Fallback rankings based on known popular models."""
    now = datetime.now().isoformat()
    
    # Based on typical OpenRouter usage patterns
    overall = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3.5-haiku",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-exp:free",
        "google/gemini-2.5-flash-preview-05-20",
        "deepseek/deepseek-chat-v3-0324:free",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-72b-instruct",
        "anthropic/claude-3-opus",
        "openai/o1-mini",
        "openai/o3-mini",
        "x-ai/grok-2-1212",
        "mistralai/mistral-large",
        "cohere/command-r-plus",
    ]
    
    programming = [
        "anthropic/claude-3.5-sonnet",
        "deepseek/deepseek-chat-v3-0324:free",
        "openai/gpt-4o",
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen-2.5-coder-32b-instruct",
        "openai/o1-mini",
        "meta-llama/codellama-70b-instruct",
        "anthropic/claude-3.5-haiku",
        "deepseek/deepseek-coder",
        "kwaicoder/kwaicoder-ds-v1:free",
    ]
    
    tool_calls = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-exp:free",
        "anthropic/claude-3.5-haiku",
        "deepseek/deepseek-chat-v3-0324:free",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.3-70b-instruct",
    ]
    
    results = {}
    for category, models in [("overall", overall), ("programming", programming), ("tool_calls", tool_calls)]:
        results[category] = [
            RankedModel(
                model_id=m,
                rank=i + 1,
                category=category,
                is_free=":free" in m.lower(),
                scraped_at=now
            )
            for i, m in enumerate(models)
        ]
    
    return results


async def update_rankings():
    """Scrape and update rankings database."""
    print("🔄 Scraping OpenRouter rankings...")
    rankings_data = await scrape_rankings_with_playwright()
    
    db = OpenRouterRankings()
    
    for category, models in rankings_data.items():
        if models:
            db.set_rankings(category, models)
    
    db.save()
    
    print(f"\n✅ Rankings updated!")
    print(f"   Overall: {len(rankings_data.get('overall', []))} models")
    print(f"   Programming: {len(rankings_data.get('programming', []))} models")
    print(f"   Tool Calls: {len(rankings_data.get('tool_calls', []))} models")


def get_rankings() -> OpenRouterRankings:
    """Get the rankings database."""
    return OpenRouterRankings()


def filter_top_openrouter_models(
    models: List[str],
    include_top_overall: int = 20,
    include_top_programming: int = 15,
    include_top_tool_calls: int = 10
) -> List[str]:
    """
    Filter OpenRouter models to only include top-ranked ones.
    
    Returns models that appear in any of the ranking categories.
    """
    db = OpenRouterRankings()
    
    top_overall = set(db.get_top_models("overall", include_top_overall))
    top_programming = set(db.get_top_models("programming", include_top_programming))
    top_tool_calls = set(db.get_top_models("tool_calls", include_top_tool_calls))
    
    all_top = top_overall | top_programming | top_tool_calls
    
    # Also include any free models (they're always relevant)
    filtered = []
    for m in models:
        if m in all_top or ":free" in m.lower() or m.endswith(":free"):
            filtered.append(m)
    
    return filtered


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenRouter Rankings Scraper")
    parser.add_argument("--scrape", action="store_true", help="Scrape latest rankings")
    parser.add_argument("--show", action="store_true", help="Show current rankings")
    
    args = parser.parse_args()
    
    if args.scrape:
        asyncio.run(update_rankings())
    elif args.show:
        db = OpenRouterRankings()
        print("\n🏆 OpenRouter Rankings\n")
        
        for category in ["overall", "programming", "tool_calls"]:
            print(f"─── {category.upper()} ───")
            models = db.get_top_models(category, 10)
            for i, m in enumerate(models, 1):
                free = "🆓" if ":free" in m else ""
                print(f"  {i:2}. {m} {free}")
            print()
    else:
        parser.print_help()
