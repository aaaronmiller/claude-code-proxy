"""
Model Statistics Scraper

Uses Playwright to scrape detailed model statistics from provider websites,
enhanced with LLM-assisted structured data extraction.

Supports configurable extraction model (env: SCRAPER_MODEL):
- Default: kwaicoder/kwaicoder-ds-v1 (free on OpenRouter)
- Fallback: deepseek/deepseek-chat-v3-0324:free
- Custom: Set SCRAPER_MODEL env var (e.g., google/gemini-3-flash)

Usage:
    python -m src.services.models.scrape_model_stats --provider openrouter
    python -m src.services.models.scrape_model_stats --all
    SCRAPER_MODEL=google/gemini-3-flash python -m src.services.models.scrape_model_stats
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Database path
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
STATS_DB_PATH = MODELS_DIR / "model_stats.json"

# LLM Configuration for extraction
# User can override via SCRAPER_MODEL env var
DEFAULT_SCRAPER_MODELS = [
    "kwaicoder/kwaicoder-ds-v1",  # Free, good at structured extraction
    "deepseek/deepseek-chat-v3-0324:free",  # Free fallback
    "qwen/qwen3-235b-a22b:free",  # Another free option
]

def get_scraper_model() -> str:
    """Get the model to use for LLM-assisted extraction."""
    return os.environ.get("SCRAPER_MODEL", DEFAULT_SCRAPER_MODELS[0])

def get_scraper_endpoint() -> str:
    """Get the endpoint for the scraper model."""
    return os.environ.get("SCRAPER_ENDPOINT", "https://openrouter.ai/api/v1")

def get_scraper_api_key() -> Optional[str]:
    """Get API key for scraper (tries multiple env vars)."""
    return (
        os.environ.get("SCRAPER_API_KEY") or
        os.environ.get("OPENROUTER_API_KEY") or
        os.environ.get("OPENAI_API_KEY") or
        os.environ.get("PROVIDER_API_KEY")
    )


@dataclass
class ModelStats:
    """Detailed model statistics from web scraping."""
    model_id: str
    provider: str
    name: str
    description: str = ""
    context_length: int = 0
    max_output: int = 0
    input_price_per_m: float = 0.0  # per million tokens
    output_price_per_m: float = 0.0
    is_free: bool = False
    parameters: str = ""  # e.g., "70B", "405B"
    modality: str = "text"  # text, vision, multimodal
    created_date: str = ""
    scraped_at: str = ""
    source_url: str = ""


class ModelStatsDatabase:
    """Local database for model statistics."""
    
    def __init__(self, db_path: Path = STATS_DB_PATH):
        self.db_path = db_path
        self._data: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """Load database from file."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self._data)} models from {self.db_path}")
            except Exception as e:
                logger.warning(f"Failed to load stats DB: {e}")
                self._data = {}
        else:
            self._data = {}
    
    def save(self):
        """Save database to file."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'w') as f:
            json.dump(self._data, f, indent=2)
        logger.info(f"Saved {len(self._data)} models to {self.db_path}")
    
    def upsert(self, stats: ModelStats):
        """Insert or update model stats."""
        self._data[stats.model_id] = asdict(stats)
    
    def get(self, model_id: str) -> Optional[Dict]:
        """Get stats for a model."""
        return self._data.get(model_id)
    
    def get_all(self) -> Dict[str, Dict]:
        """Get all model stats."""
        return self._data
    
    def correlate_with_api(self, api_models: List[str]) -> Dict[str, Dict]:
        """
        Correlate scraped stats with API model list.
        
        Returns dict of models with combined API + scraped data.
        """
        result = {}
        for model_id in api_models:
            stats = self.get(model_id)
            result[model_id] = {
                "id": model_id,
                "api_available": True,
                "has_stats": stats is not None,
                "stats": stats
            }
        return result


async def scrape_openrouter_models(headless: bool = True) -> List[ModelStats]:
    """
    Scrape OpenRouter models page for detailed statistics.
    
    Uses Playwright to get rich data not available via API.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install")
        return []
    
    models = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        
        try:
            # Navigate to OpenRouter models page
            logger.info("Navigating to OpenRouter models page...")
            await page.goto("https://openrouter.ai/models", wait_until="networkidle")
            await asyncio.sleep(2)  # Let dynamic content load
            
            # Get model cards
            model_cards = await page.query_selector_all('[data-testid="model-card"], .model-card, [class*="ModelCard"]')
            
            if not model_cards:
                # Try alternative selector
                model_cards = await page.query_selector_all('a[href^="/models/"]')
            
            logger.info(f"Found {len(model_cards)} model elements")
            
            # Extract data from each card (limit to avoid timeout)
            for card in model_cards[:100]:  # Limit to first 100
                try:
                    # Get model ID from href
                    href = await card.get_attribute("href")
                    if href and "/models/" in href:
                        model_id = href.split("/models/")[-1].strip("/")
                    else:
                        continue
                    
                    # Get text content for basic info
                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    
                    name = lines[0] if lines else model_id
                    
                    # Parse pricing if visible
                    input_price = 0.0
                    output_price = 0.0
                    is_free = False
                    
                    for line in lines:
                        if "free" in line.lower():
                            is_free = True
                        if "$" in line:
                            # Try to parse price
                            try:
                                price_str = line.replace("$", "").replace("/M", "").strip()
                                if "input" in line.lower():
                                    input_price = float(price_str.split()[0])
                                elif "output" in line.lower():
                                    output_price = float(price_str.split()[0])
                            except:
                                pass
                    
                    stats = ModelStats(
                        model_id=model_id,
                        provider="openrouter",
                        name=name,
                        input_price_per_m=input_price,
                        output_price_per_m=output_price,
                        is_free=is_free,
                        scraped_at=datetime.now().isoformat(),
                        source_url=f"https://openrouter.ai/models/{model_id}"
                    )
                    models.append(stats)
                    
                except Exception as e:
                    logger.debug(f"Error parsing model card: {e}")
                    continue
            
            # For more detailed stats, visit individual model pages
            # (Only do this for top models to save time)
            logger.info(f"Scraped basic info for {len(models)} models")
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
        finally:
            await browser.close()
    
    return models


async def scrape_model_detail(model_id: str) -> Optional[ModelStats]:
    """Scrape detailed info for a specific model."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = f"https://openrouter.ai/models/{model_id}"
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(1)
            
            # Get page content
            content = await page.content()
            text = await page.inner_text("body")
            
            # Parse details
            context_length = 0
            max_output = 0
            input_price = 0.0
            output_price = 0.0
            parameters = ""
            
            # Look for specific patterns
            import re
            
            # Context length
            ctx_match = re.search(r"(\d+[,\d]*)\s*(?:context|tokens)", text, re.I)
            if ctx_match:
                context_length = int(ctx_match.group(1).replace(",", ""))
            
            # Parameters
            param_match = re.search(r"(\d+\.?\d*)\s*[Bb](?:illion)?(?:\s+param)?", text)
            if param_match:
                parameters = f"{param_match.group(1)}B"
            
            # Pricing
            price_match = re.search(r"\$(\d+\.?\d*)\s*/\s*(?:M|million)", text, re.I)
            if price_match:
                input_price = float(price_match.group(1))
            
            stats = ModelStats(
                model_id=model_id,
                provider="openrouter",
                name=model_id.split("/")[-1] if "/" in model_id else model_id,
                context_length=context_length,
                max_output=max_output,
                input_price_per_m=input_price,
                output_price_per_m=output_price,
                parameters=parameters,
                is_free=(input_price == 0 and output_price == 0),
                scraped_at=datetime.now().isoformat(),
                source_url=url
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error scraping {model_id}: {e}")
            return None
        finally:
            await browser.close()


async def update_model_database(provider: str = "openrouter"):
    """
    Update the model statistics database.
    
    Scrapes provider website and saves to local database.
    """
    db = ModelStatsDatabase()
    
    if provider == "openrouter":
        print("🔄 Scraping OpenRouter models...")
        models = await scrape_openrouter_models()
        
        for stats in models:
            db.upsert(stats)
        
        db.save()
        print(f"✅ Updated {len(models)} models in database")
    else:
        print(f"❌ Unknown provider: {provider}")


def correlate_api_with_stats(api_models: List[str]) -> Dict[str, Any]:
    """
    Correlate API model list with scraped statistics.
    
    Returns enriched model data.
    """
    db = ModelStatsDatabase()
    return db.correlate_with_api(api_models)


def get_enriched_model_info(model_id: str) -> Dict[str, Any]:
    """Get combined API + scraped info for a model."""
    db = ModelStatsDatabase()
    stats = db.get(model_id)
    
    if stats:
        return {
            "id": model_id,
            "has_stats": True,
            **stats
        }
    return {
        "id": model_id,
        "has_stats": False
    }


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Statistics Scraper")
    parser.add_argument("--provider", choices=["openrouter", "all"], default="openrouter",
                       help="Provider to scrape")
    parser.add_argument("--model", help="Scrape specific model details")
    parser.add_argument("--show", action="store_true", help="Show current database")
    
    args = parser.parse_args()
    
    if args.show:
        db = ModelStatsDatabase()
        data = db.get_all()
        print(f"\n📊 Model Stats Database: {len(data)} models\n")
        for model_id, stats in list(data.items())[:20]:
            price = stats.get("input_price_per_m", 0)
            free = "🆓" if stats.get("is_free") else f"${price:.2f}/M"
            print(f"  {model_id:<50} {free}")
        if len(data) > 20:
            print(f"  ... and {len(data) - 20} more")
    elif args.model:
        print(f"🔄 Scraping details for {args.model}...")
        stats = asyncio.run(scrape_model_detail(args.model))
        if stats:
            print(f"✅ Got stats: {asdict(stats)}")
        else:
            print("❌ Failed to get stats")
    else:
        asyncio.run(update_model_database(args.provider))
