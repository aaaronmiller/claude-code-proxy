"""
Deep Web Scraper: Conditional scraping for OpenRouter model pages.
Implements: browser management, stealth configuration, page fetching, benchmark extraction.

Uses: camoufox (stealth browser) and crawl4AI (LLM-powered extraction).
"""

import asyncio
import logging
import random
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from camoufox.sync_api import Camoufox
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

from openrouter_model_scout.models import Performance, Benchmarks, IntelligenceMetrics, CodingMetrics, AgenticMetrics
from openrouter_model_scout.exceptions import ScraperError

logger = logging.getLogger(__name__)


class ScrapeResult(BaseModel):
    """Result of scraping a single model page."""
    model_id: str
    benchmarks: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    description_short: Optional[str] = None
    description_full: Optional[str] = None
    release_date: Optional[str] = None
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None


class ScraperManager:
    """
    Manages the deep scraper for OpenRouter model pages.

    Handles browser lifecycle, rate limiting, and extraction.
    """

    def __init__(
        self,
        stealth_mode: bool = True,
        max_concurrent: int = 1,
        delay_range: tuple[float, float] = (2.0, 5.0)
    ):
        """
        Initialize scraper manager.

        Args:
            stealth_mode: Enable stealth features (random delays, user-agent rotation)
            max_concurrent: Maximum concurrent browser instances (keep at 1 for stealth)
            delay_range: Min/max seconds between page loads (for rate limiting)
        """
        self.stealth_mode = stealth_mode
        self.max_concurrent = max_concurrent
        self.delay_range = delay_range
        self._browser: Optional[Camoufox] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def __enter__(self):
        """Context manager entry: start browser."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: close browser."""
        self.stop()

    def start(self) -> None:
        """Initialize the browser."""
        if self._browser is None:
            logger.info("Starting Camoufox browser...")
            # Camoufox has stealth built-in by default; no extra parameters needed
            self._browser = Camoufox(headless=True)  # type: ignore[call-arg]
            self._browser.__enter__()  # Explicit context enter
            logger.info("Browser started successfully")

    def stop(self) -> None:
        """Close the browser."""
        if self._browser is not None:
            logger.info("Stopping Camoufox browser...")
            try:
                self._browser.__exit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self._browser = None

    async def fetch_model_page(
        self,
        model_id: str,
        base_url: str = "https://openrouter.ai"
    ) -> ScrapeResult:
        """
        Fetch and extract data from a model's page.

        Args:
            model_id: Model identifier (e.g., "openai/gpt-4")
            base_url: Base OpenRouter URL

        Returns:
            ScrapeResult with extracted data

        Raises:
            ScraperError: If extraction fails
        """
        async with self._semaphore:
            # Apply stealth delay
            if self.stealth_mode:
                delay = random.uniform(*self.delay_range)
                await asyncio.sleep(delay)

            url = f"{base_url.rstrip('/')}/{model_id}"

            logger.debug(f"Fetching {url}")

            try:
                # Use crawl4AI for robust extraction
                result = await self._crawl_with_crawl4ai(url)
                return ScrapeResult(model_id=model_id, **result)

            except Exception as e:
                logger.error(f"Failed to scrape {model_id}: {e}")
                raise ScraperError(f"Scrape failed for {model_id}: {e}") from e

    async def _crawl_with_crawl4ai(self, url: str) -> Dict[str, Any]:
        """
        Use crawl4AI to extract structured data from page.

        Args:
            url: Target URL

        Returns:
            Dictionary with extracted fields
        """
        # Configure extraction strategy
        extraction_strategy = LLMExtractionStrategy(
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            api_key=None,  # Use environment variable
            temperature=0.0,
            max_tokens=2000,
        )

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True,
                # Use the camoufox browser if possible, or fallback to default
            )

            if not result.extracted_content:
                raise ScraperError("No content extracted")

            # Parse the extracted JSON
            try:
                # crawl4AI returns a JSON string - parse it
                import json
                data = json.loads(result.extracted_content)
                return self._normalize_extracted_data(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse extracted JSON: {e}")
                return {}

    def _normalize_extracted_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw extraction results into expected fields.

        The LLM extraction might return various field names; map to our schema.
        """
        normalized = {}

        # Benchmarks
        bench_fields = ['benchmarks', 'benchmark', 'scores', 'metrics']
        for field in bench_fields:
            if field in raw and isinstance(raw[field], dict):
                normalized['benchmarks'] = raw[field]
                break

        # Performance
        perf_fields = ['performance', 'perf', 'throughput', 'latency']
        for field in perf_fields:
            if field in raw and isinstance(raw[field], dict):
                normalized['performance'] = raw[field]
                break

        # Description fields
        if 'description_short' in raw:
            normalized['description_short'] = raw['description_short']
        if 'description_full' in raw:
            normalized['description_full'] = raw['description_full']
        if 'release_date' in raw:
            normalized['release_date'] = raw['release_date']
        if 'parameter_size' in raw:
            normalized['parameter_size'] = raw['parameter_size']
        if 'quantization' in raw:
            normalized['quantization'] = raw['quantization']

        return normalized


def estimate_scrape_cost(model_id: str, approx_tokens: int = 500) -> Dict[str, int]:
    """
    Estimate token usage for a single scrape operation.

    Args:
        model_id: Model being scraped
        approx_tokens: Approximate tokens used by crawl4AI LLM extraction

    Returns:
        Dict with prompt_tokens, completion_tokens
    """
    # For LLM-based extraction, there's a prompt (page content) and completion (structured JSON)
    # Rough estimate: prompt = page HTML (~10KB tokens), completion = output (~500 tokens)
    # Since we're using crawl4AI with LLM extraction strategy, we need to track both
    prompt_tokens = 8000  # Approximate HTML page size in tokens
    completion_tokens = approx_tokens

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def parse_benchmark_scores(data: Dict[str, Any]) -> Benchmarks:
    """
    Parse benchmark data from scraped content into structured Benchmarks object.

    Args:
        data: Raw scraped benchmark dict

    Returns:
        Benchmarks object (may have missing fields if data incomplete)
    """
    bench_data = {}

    # Intelligence
    if 'intelligence' in data:
        intel = data['intelligence']
        if isinstance(intel, dict):
            bench_data['intelligence'] = IntelligenceMetrics(
                score=float(intel.get('score', 0)),
                percentile=float(intel.get('percentile', 0))
            )

    # Coding
    if 'coding' in data:
        coding = data['coding']
        if isinstance(coding, dict):
            bench_data['coding'] = CodingMetrics(
                score=float(coding.get('score', 0)),
                percentile=float(coding.get('percentile', 0))
            )

    # Agentic
    if 'agentic' in data:
        agentic = data['agentic']
        if isinstance(agentic, dict):
            bench_data['agentic'] = AgenticMetrics(
                score=float(agentic.get('score', 0)),
                percentile=float(agentic.get('percentile', 0))
            )

    return Benchmarks(**bench_data)


def parse_performance_metrics(data: Dict[str, Any]) -> Optional[Performance]:
    """
    Parse performance metrics from scraped data.

    Args:
        data: Raw scraped performance dict

    Returns:
        Performance object or None if no data
    """
    perf_fields = ['throughput_tps', 'latency_seconds', 'e2e_latency_seconds', 'tool_error_rate', 'uptime_percent']
    if not any(field in data for field in perf_fields):
        return None

    perf_kwargs = {}
    for field in perf_fields:
        if field in data:
            try:
                perf_kwargs[field] = float(data[field])
            except (ValueError, TypeError):
                pass

    return Performance(**perf_kwargs) if perf_kwargs else None


async def process_model_queue(
    model_ids: List[str],
    manager: ScraperManager,
    max_retries: int = 3,
    initial_backoff: float = 1.0
) -> Dict[str, ScrapeResult]:
    """
    Process a queue of model IDs, scraping each with retry logic.
    """
    results = {}

    for model_id in model_ids:
        retries = 0
        backoff = initial_backoff

        while retries <= max_retries:
            try:
                logger.info(f"Scraping model {model_id} (attempt {retries + 1}/{max_retries + 1})")
                result = await manager.fetch_model_page(model_id)
                results[model_id] = result
                logger.info(f"Successfully scraped {model_id}")
                break
            except ScraperError as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f"Failed to scrape {model_id} after {max_retries} retries: {e}")
                    break
                else:
                    jitter = random.uniform(0, 0.1 * backoff)
                    wait_time = backoff + jitter
                    logger.warning(f"Scrape failed for {model_id}, retrying in {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
                    backoff *= 2

        if model_id != model_ids[-1]:
            await asyncio.sleep(0.5)

    return results


def convert_scrape_results_to_enrichment(
    results: Dict[str, ScrapeResult]
) -> Dict[str, Dict[str, Any]]:
    """
    Convert ScrapeResult objects into enrichment dict for normalizer.
    """
    enrichment = {}

    for model_id, result in results.items():
        data = {}

        if result.benchmarks:
            data['benchmarks'] = result.benchmarks
        if result.performance:
            data['performance'] = result.performance
        if result.description_short:
            data['description_short'] = result.description_short
        if result.description_full:
            data['description_full'] = result.description_full
        if result.release_date:
            data['release_date'] = result.release_date
        if result.parameter_size:
            data['parameter_size'] = result.parameter_size
        if result.quantization:
            data['quantization'] = result.quantization

        if data:
            enrichment[model_id] = data

    return enrichment
