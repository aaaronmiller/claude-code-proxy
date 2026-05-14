# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/scrape_model_stats.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/scrape_model_stats.py`

**Module Overview**: 
```text
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
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `MODELS_DIR` = `Path(__file__).parent.parent.parent / 'models'`
- `STATS_DB_PATH` = `MODELS_DIR / 'model_stats.json'`
- `DEFAULT_SCRAPER_MODELS` = `['kwaicoder/kwaicoder-ds-v1', 'deepseek/deepseek-chat-v3-0324:free', 'qwen/qwen3-235b-a22b:free']`

## Dependencies & Imports
asyncio, json, logging, os, sys, datetime.datetime, pathlib.Path, typing.Dict, typing.List, typing.Optional, typing.Any, dataclasses.dataclass, dataclasses.asdict

## Feature Function: `get_scraper_model`
**Logic & Purpose:**
```text
Get the model to use for LLM-assisted extraction.
```

**Parameters:** ``
**Implementation:**
```python
def get_scraper_model() -> str:
    """Get the model to use for LLM-assisted extraction."""
    return os.environ.get('SCRAPER_MODEL', DEFAULT_SCRAPER_MODELS[0])
```

---

## Feature Function: `get_scraper_endpoint`
**Logic & Purpose:**
```text
Get the endpoint for the scraper model.
```

**Parameters:** ``
**Implementation:**
```python
def get_scraper_endpoint() -> str:
    """Get the endpoint for the scraper model."""
    return os.environ.get('SCRAPER_ENDPOINT', 'https://openrouter.ai/api/v1')
```

---

## Feature Function: `get_scraper_api_key`
**Logic & Purpose:**
```text
Get API key for scraper (tries multiple env vars).
```

**Parameters:** ``
**Implementation:**
```python
def get_scraper_api_key() -> Optional[str]:
    """Get API key for scraper (tries multiple env vars)."""
    return os.environ.get('SCRAPER_API_KEY') or os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('PROVIDER_API_KEY')
```

---

## Feature Class: `ModelStats`
**Description:**
```text
Detailed model statistics from web scraping.
```

---

## Feature Class: `ModelStatsDatabase`
**Description:**
```text
Local database for model statistics.
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: Path=STATS_DB_PATH):
    self.db_path = db_path
    self._data: Dict[str, Dict] = {}
    self._load()
```

### Method: `_load`
**Logic & Purpose:**
```text
Load database from file.
```

**Parameters:** `self`
**Implementation:**
```python
def _load(self):
    """Load database from file."""
    if self.db_path.exists():
        try:
            with open(self.db_path, 'r') as f:
                self._data = json.load(f)
            logger.info(f'Loaded {len(self._data)} models from {self.db_path}')
        except Exception as e:
            logger.warning(f'Failed to load stats DB: {e}')
            self._data = {}
    else:
        self._data = {}
```

### Method: `save`
**Logic & Purpose:**
```text
Save database to file.
```

**Parameters:** `self`
**Implementation:**
```python
def save(self):
    """Save database to file."""
    self.db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(self.db_path, 'w') as f:
        json.dump(self._data, f, indent=2)
    logger.info(f'Saved {len(self._data)} models to {self.db_path}')
```

### Method: `upsert`
**Logic & Purpose:**
```text
Insert or update model stats.
```

**Parameters:** `self, stats`
**Implementation:**
```python
def upsert(self, stats: ModelStats):
    """Insert or update model stats."""
    self._data[stats.model_id] = asdict(stats)
```

### Method: `get`
**Logic & Purpose:**
```text
Get stats for a model.
```

**Parameters:** `self, model_id`
**Implementation:**
```python
def get(self, model_id: str) -> Optional[Dict]:
    """Get stats for a model."""
    return self._data.get(model_id)
```

### Method: `get_all`
**Logic & Purpose:**
```text
Get all model stats.
```

**Parameters:** `self`
**Implementation:**
```python
def get_all(self) -> Dict[str, Dict]:
    """Get all model stats."""
    return self._data
```

### Method: `correlate_with_api`
**Logic & Purpose:**
```text
Correlate scraped stats with API model list.

Returns dict of models with combined API + scraped data.
```

**Parameters:** `self, api_models`
**Variables Used:** `stats, result`
**Implementation:**
```python
def correlate_with_api(self, api_models: List[str]) -> Dict[str, Dict]:
    """
        Correlate scraped stats with API model list.
        
        Returns dict of models with combined API + scraped data.
        """
    result = {}
    for model_id in api_models:
        stats = self.get(model_id)
        result[model_id] = {'id': model_id, 'api_available': True, 'has_stats': stats is not None, 'stats': stats}
    return result
```

---

## Feature Function: `scrape_openrouter_models`
**Logic & Purpose:**
```text
Scrape OpenRouter models page for detailed statistics.

Uses Playwright to get rich data not available via API.
```

**Parameters:** `headless`
**Variables Used:** `page, text, model_id, price_str, href, lines, is_free, stats, model_cards, models, output_price, input_price, name, browser`
**Implementation:**
```python
async def scrape_openrouter_models(headless: bool=True) -> List[ModelStats]:
    """
    Scrape OpenRouter models page for detailed statistics.
    
    Uses Playwright to get rich data not available via API.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error('Playwright not installed. Run: pip install playwright && playwright install')
        return []
    models = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            logger.info('Navigating to OpenRouter models page...')
            await page.goto('https://openrouter.ai/models', wait_until='networkidle')
            await asyncio.sleep(2)
            model_cards = await page.query_selector_all('[data-testid="model-card"], .model-card, [class*="ModelCard"]')
            if not model_cards:
                model_cards = await page.query_selector_all('a[href^="/models/"]')
            logger.info(f'Found {len(model_cards)} model elements')
            for card in model_cards[:100]:
                try:
                    href = await card.get_attribute('href')
                    if href and '/models/' in href:
                        model_id = href.split('/models/')[-1].strip('/')
                    else:
                        continue
                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    name = lines[0] if lines else model_id
                    input_price = 0.0
                    output_price = 0.0
                    is_free = False
                    for line in lines:
                        if 'free' in line.lower():
                            is_free = True
                        if '$' in line:
                            try:
                                price_str = line.replace('$', '').replace('/M', '').strip()
                                if 'input' in line.lower():
                                    input_price = float(price_str.split()[0])
                                elif 'output' in line.lower():
                                    output_price = float(price_str.split()[0])
                            except Exception as _e:
                                pass
                    stats = ModelStats(model_id=model_id, provider='openrouter', name=name, input_price_per_m=input_price, output_price_per_m=output_price, is_free=is_free, scraped_at=datetime.now().isoformat(), source_url=f'https://openrouter.ai/models/{model_id}')
                    models.append(stats)
                except Exception as e:
                    logger.debug(f'Error parsing model card: {e}')
                    continue
            logger.info(f'Scraped basic info for {len(models)} models')
        except Exception as e:
            logger.error(f'Scraping error: {e}')
        finally:
            await browser.close()
    return models
```

---

## Feature Function: `scrape_model_detail`
**Logic & Purpose:**
```text
Scrape detailed info for a specific model.
```

**Parameters:** `model_id`
**Variables Used:** `max_output, page, context_length, url, text, ctx_match, param_match, stats, parameters, content, output_price, price_match, input_price, browser`
**Implementation:**
```python
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
            url = f'https://openrouter.ai/models/{model_id}'
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(1)
            content = await page.content()
            text = await page.inner_text('body')
            context_length = 0
            max_output = 0
            input_price = 0.0
            output_price = 0.0
            parameters = ''
            import re
            ctx_match = re.search('(\\d+[,\\d]*)\\s*(?:context|tokens)', text, re.I)
            if ctx_match:
                context_length = int(ctx_match.group(1).replace(',', ''))
            param_match = re.search('(\\d+\\.?\\d*)\\s*[Bb](?:illion)?(?:\\s+param)?', text)
            if param_match:
                parameters = f'{param_match.group(1)}B'
            price_match = re.search('\\$(\\d+\\.?\\d*)\\s*/\\s*(?:M|million)', text, re.I)
            if price_match:
                input_price = float(price_match.group(1))
            stats = ModelStats(model_id=model_id, provider='openrouter', name=model_id.split('/')[-1] if '/' in model_id else model_id, context_length=context_length, max_output=max_output, input_price_per_m=input_price, output_price_per_m=output_price, parameters=parameters, is_free=input_price == 0 and output_price == 0, scraped_at=datetime.now().isoformat(), source_url=url)
            return stats
        except Exception as e:
            logger.error(f'Error scraping {model_id}: {e}')
            return None
        finally:
            await browser.close()
```

---

## Feature Function: `update_model_database`
**Logic & Purpose:**
```text
Update the model statistics database.

Scrapes provider website and saves to local database.
```

**Parameters:** `provider`
**Variables Used:** `db, models`
**Implementation:**
```python
async def update_model_database(provider: str='openrouter'):
    """
    Update the model statistics database.
    
    Scrapes provider website and saves to local database.
    """
    db = ModelStatsDatabase()
    if provider == 'openrouter':
        print('🔄 Scraping OpenRouter models...')
        models = await scrape_openrouter_models()
        for stats in models:
            db.upsert(stats)
        db.save()
        print(f'✅ Updated {len(models)} models in database')
    else:
        print(f'❌ Unknown provider: {provider}')
```

---

## Feature Function: `correlate_api_with_stats`
**Logic & Purpose:**
```text
Correlate API model list with scraped statistics.

Returns enriched model data.
```

**Parameters:** `api_models`
**Variables Used:** `db`
**Implementation:**
```python
def correlate_api_with_stats(api_models: List[str]) -> Dict[str, Any]:
    """
    Correlate API model list with scraped statistics.
    
    Returns enriched model data.
    """
    db = ModelStatsDatabase()
    return db.correlate_with_api(api_models)
```

---

## Feature Function: `get_enriched_model_info`
**Logic & Purpose:**
```text
Get combined API + scraped info for a model.
```

**Parameters:** `model_id`
**Variables Used:** `stats, db`
**Implementation:**
```python
def get_enriched_model_info(model_id: str) -> Dict[str, Any]:
    """Get combined API + scraped info for a model."""
    db = ModelStatsDatabase()
    stats = db.get(model_id)
    if stats:
        return {'id': model_id, 'has_stats': True, **stats}
    return {'id': model_id, 'has_stats': False}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/provider_models.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/provider_models.py`

**Module Overview**: 
```text
Provider Model Fetcher

Fetches available models from each configured provider endpoint using live API calls.
This validates API keys and gets real-time model availability.

Supports:
- VibeProxy (local Gemini proxy)
- OpenRouter
- OpenAI
- Anthropic
- Any OpenAI-compatible endpoint
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
asyncio, httpx, os, json, typing.Dict, typing.List, typing.Optional, typing.Tuple, typing.Any, dataclasses.dataclass, enum.Enum, logging

## Feature Class: `ModelInfo`
**Description:**
```text
Information about a model with full statistics.
```

### Method: `__post_init__`
**Parameters:** `self`
**Implementation:**
```python
def __post_init__(self):
    if self.input_modalities is None:
        self.input_modalities = ['text']
    if self.output_modalities is None:
        self.output_modalities = ['text']
    if self.supported_parameters is None:
        self.supported_parameters = []
```

---

## Feature Class: `EndpointStatus`
**Description:**
```text
Status of an endpoint check.
```

---

## Feature Class: `ProviderModelFetcher`
**Description:**
```text
Fetches models from provider endpoints.
```

### Method: `__init__`
**Parameters:** `self, timeout`
**Implementation:**
```python
def __init__(self, timeout: float=10.0):
    self.timeout = timeout
    self.client = httpx.AsyncClient(timeout=timeout)
```

### Method: `close`
**Parameters:** `self`
**Implementation:**
```python
async def close(self):
    await self.client.aclose()
```

### Method: `fetch_models`
**Logic & Purpose:**
```text
Fetch available models from an endpoint.

Args:
    endpoint: API endpoint URL (e.g., http://127.0.0.1:8317/v1)
    api_key: Optional API key (uses global key if not provided)
    
Returns:
    EndpointStatus with connection status and model list
```

**Parameters:** `self, endpoint, api_key`
**Variables Used:** `provider`
**Implementation:**
```python
async def fetch_models(self, endpoint: str, api_key: Optional[str]=None) -> EndpointStatus:
    """
        Fetch available models from an endpoint.
        
        Args:
            endpoint: API endpoint URL (e.g., http://127.0.0.1:8317/v1)
            api_key: Optional API key (uses global key if not provided)
            
        Returns:
            EndpointStatus with connection status and model list
        """
    provider = self._detect_provider(endpoint)
    try:
        if provider == 'openrouter':
            return await self._fetch_openrouter_models(endpoint, api_key)
        elif provider == 'anthropic':
            return await self._fetch_anthropic_models(endpoint, api_key)
        else:
            return await self._fetch_openai_models(endpoint, api_key, provider)
    except httpx.TimeoutException:
        return EndpointStatus(endpoint=endpoint, provider=provider, is_connected=False, api_key_valid=False, models=[], error='Connection timeout')
    except httpx.ConnectError as e:
        return EndpointStatus(endpoint=endpoint, provider=provider, is_connected=False, api_key_valid=False, models=[], error=f'Connection failed: {str(e)}')
    except Exception as e:
        return EndpointStatus(endpoint=endpoint, provider=provider, is_connected=False, api_key_valid=False, models=[], error=str(e))
```

### Method: `_detect_provider`
**Logic & Purpose:**
```text
Detect provider from endpoint URL.
```

**Parameters:** `self, endpoint`
**Variables Used:** `url_lower`
**Implementation:**
```python
def _detect_provider(self, endpoint: str) -> str:
    """Detect provider from endpoint URL."""
    url_lower = endpoint.lower()
    if 'openrouter.ai' in url_lower:
        return 'openrouter'
    elif 'api.anthropic.com' in url_lower:
        return 'anthropic'
    elif 'api.openai.com' in url_lower:
        return 'openai'
    elif '.openai.azure.com' in url_lower:
        return 'azure'
    elif '127.0.0.1' in url_lower or 'localhost' in url_lower:
        return 'vibeproxy'
    else:
        return 'openai_compatible'
```

### Method: `_fetch_openai_models`
**Logic & Purpose:**
```text
Fetch models from OpenAI-compatible endpoint.
```

**Parameters:** `self, endpoint, api_key, provider`
**Variables Used:** `models_url, data, base_url, headers, model_id, models, response`
**Implementation:**
```python
async def _fetch_openai_models(self, endpoint: str, api_key: Optional[str], provider: str) -> EndpointStatus:
    """Fetch models from OpenAI-compatible endpoint."""
    base_url = endpoint.rstrip('/')
    if not base_url.endswith('/v1'):
        if '/v1' not in base_url:
            base_url += '/v1'
    models_url = f'{base_url}/models'
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    response = await self.client.get(models_url, headers=headers)
    if response.status_code == 401:
        return EndpointStatus(endpoint=endpoint, provider=provider, is_connected=True, api_key_valid=False, models=[], error='Invalid API key')
    if response.status_code != 200:
        return EndpointStatus(endpoint=endpoint, provider=provider, is_connected=True, api_key_valid=True, models=[], error=f'HTTP {response.status_code}')
    data = response.json()
    models = []
    for model in data.get('data', []):
        model_id = model.get('id', '')
        models.append(ModelInfo(id=model_id, name=model.get('name', model_id), provider=provider, context_length=model.get('context_length', 128000), max_output=model.get('max_output', 4096), created=model.get('created', 0)))
    return EndpointStatus(endpoint=endpoint, provider=provider, is_connected=True, api_key_valid=True, models=models)
```

### Method: `_fetch_openrouter_models`
**Logic & Purpose:**
```text
Fetch models from OpenRouter with pricing data.
```

**Parameters:** `self, endpoint, api_key`
**Variables Used:** `models_url, completion_price, data, context, headers, model_id, architecture, pricing, top_provider, prompt_price, models, response`
**Implementation:**
```python
async def _fetch_openrouter_models(self, endpoint: str, api_key: Optional[str]) -> EndpointStatus:
    """Fetch models from OpenRouter with pricing data."""
    models_url = 'https://openrouter.ai/api/v1/models'
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    response = await self.client.get(models_url, headers=headers)
    if response.status_code == 401:
        return EndpointStatus(endpoint=endpoint, provider='openrouter', is_connected=True, api_key_valid=False, models=[], error='Invalid API key')
    if response.status_code != 200:
        return EndpointStatus(endpoint=endpoint, provider='openrouter', is_connected=True, api_key_valid=True, models=[], error=f'HTTP {response.status_code}')
    data = response.json()
    models = []
    for model in data.get('data', []):
        model_id = model.get('id', '')
        pricing = model.get('pricing', {})
        context = model.get('context_length', 128000)
        architecture = model.get('architecture', {})
        top_provider = model.get('top_provider', {})
        prompt_price = float(pricing.get('prompt', 0)) * 1000000
        completion_price = float(pricing.get('completion', 0)) * 1000000
        models.append(ModelInfo(id=model_id, name=model.get('name', model_id), provider='openrouter', context_length=context, max_output=top_provider.get('max_completion_tokens', 4096), pricing_input=prompt_price, pricing_output=completion_price, is_free=prompt_price == 0 and completion_price == 0, created=model.get('created', 0), description=model.get('description', '')[:500], modality=architecture.get('modality', 'text->text'), hugging_face_id=model.get('hugging_face_id', ''), input_modalities=architecture.get('input_modalities', ['text']), output_modalities=architecture.get('output_modalities', ['text']), tokenizer=architecture.get('tokenizer', ''), supported_parameters=model.get('supported_parameters', []), is_moderated=top_provider.get('is_moderated', False)))
    return EndpointStatus(endpoint=endpoint, provider='openrouter', is_connected=True, api_key_valid=True, models=models)
```

### Method: `_fetch_anthropic_models`
**Logic & Purpose:**
```text
Fetch/validate Anthropic endpoint (no /models endpoint, so we validate with a minimal request).
```

**Parameters:** `self, endpoint, api_key`
**Variables Used:** `headers, test_url, response, models`
**Implementation:**
```python
async def _fetch_anthropic_models(self, endpoint: str, api_key: Optional[str]) -> EndpointStatus:
    """Fetch/validate Anthropic endpoint (no /models endpoint, so we validate with a minimal request)."""
    headers = {'x-api-key': api_key or '', 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
    test_url = f"{endpoint.rstrip('/')}/messages"
    try:
        response = await self.client.post(test_url, headers=headers, json={'model': 'claude-3-haiku-20240307', 'max_tokens': 1, 'messages': [{'role': 'user', 'content': 'test'}]})
        if response.status_code == 401:
            return EndpointStatus(endpoint=endpoint, provider='anthropic', is_connected=True, api_key_valid=False, models=[], error='Invalid API key')
        models = [ModelInfo(id='claude-3-5-sonnet-20241022', name='Claude 3.5 Sonnet', provider='anthropic', context_length=200000, max_output=8192), ModelInfo(id='claude-3-5-haiku-20241022', name='Claude 3.5 Haiku', provider='anthropic', context_length=200000, max_output=8192), ModelInfo(id='claude-3-opus-20240229', name='Claude 3 Opus', provider='anthropic', context_length=200000, max_output=4096), ModelInfo(id='claude-sonnet-4-20250514', name='Claude Sonnet 4', provider='anthropic', context_length=200000, max_output=16384), ModelInfo(id='claude-opus-4-20250514', name='Claude Opus 4', provider='anthropic', context_length=200000, max_output=16384)]
        return EndpointStatus(endpoint=endpoint, provider='anthropic', is_connected=True, api_key_valid=True, models=models)
    except Exception as e:
        return EndpointStatus(endpoint=endpoint, provider='anthropic', is_connected=False, api_key_valid=False, models=[], error=str(e))
```

---

## Feature Function: `get_all_endpoint_models`
**Logic & Purpose:**
```text
Fetch models from all configured endpoints.

Returns:
    Dict mapping endpoint names to their status
```

**Parameters:** ``
**Variables Used:** `results, tasks, endpoints_to_check, fetcher`
**Implementation:**
```python
async def get_all_endpoint_models() -> Dict[str, EndpointStatus]:
    """
    Fetch models from all configured endpoints.
    
    Returns:
        Dict mapping endpoint names to their status
    """
    from src.core.config import config
    fetcher = ProviderModelFetcher()
    results = {}
    try:
        endpoints_to_check = []
        if config.openai_base_url:
            endpoints_to_check.append(('default', config.openai_base_url, config.openai_api_key))
        for name, entry in config.provider_registry.items():
            endpoints_to_check.append((name, entry['url'], entry.get('api_key')))
        tasks = []
        for name, endpoint, api_key in endpoints_to_check:
            tasks.append((name, fetcher.fetch_models(endpoint, api_key)))
        for name, task in tasks:
            results[name] = await task
    finally:
        await fetcher.close()
    return results
```

---

## Feature Function: `get_top_models_per_provider`
**Logic & Purpose:**
```text
Get top N models from an endpoint, sorted by popularity/capability.

For OpenRouter: Filters to only top-ranked models (overall + programming leaderboards)
For other providers: Shows all (smaller lists, no filtering needed)

Sorting priority:
1. NEW free models (created in last 30 days) - most important!
2. Other free models
3. Larger context window
4. Alphabetically by name
```

**Parameters:** `status, n, filter_openrouter`
**Variables Used:** `sorted_models, thirty_days_ago, model_ids, models, db, top_ids`
**Implementation:**
```python
def get_top_models_per_provider(status: EndpointStatus, n: int=5, filter_openrouter: bool=True) -> List[ModelInfo]:
    """
    Get top N models from an endpoint, sorted by popularity/capability.
    
    For OpenRouter: Filters to only top-ranked models (overall + programming leaderboards)
    For other providers: Shows all (smaller lists, no filtering needed)
    
    Sorting priority:
    1. NEW free models (created in last 30 days) - most important!
    2. Other free models
    3. Larger context window
    4. Alphabetically by name
    """
    import time
    models = status.models
    if status.provider == 'openrouter' and filter_openrouter:
        try:
            from src.services.models.openrouter_rankings import filter_top_openrouter_models, OpenRouterRankings
            model_ids = [m.id for m in models]
            top_ids = set(filter_top_openrouter_models(model_ids, include_top_overall=25, include_top_programming=20, include_top_tool_calls=15))
            db = OpenRouterRankings()
            if db.get_top_models('overall'):
                models = [m for m in models if m.id in top_ids or m.is_free]
        except ImportError:
            pass
    thirty_days_ago = int(time.time()) - 30 * 24 * 60 * 60

    def is_new(model: ModelInfo) -> bool:
        return model.created > thirty_days_ago
    sorted_models = sorted(models, key=lambda m: (not (m.is_free and is_new(m)), not m.is_free, -m.context_length, m.id))
    return sorted_models[:n]
```

---

## Feature Function: `format_model_display`
**Logic & Purpose:**
```text
Format a model for display in the selector.
```

**Parameters:** `model`
**Variables Used:** `price_str, name`
**Implementation:**
```python
def format_model_display(model: ModelInfo) -> str:
    """Format a model for display in the selector."""

    def fmt_tokens(n: int) -> str:
        if n >= 1000000:
            return f'{n / 1000000:.1f}M'
        elif n >= 1000:
            return f'{n / 1000:.0f}k'
        return str(n)
    if model.is_free:
        price_str = '🆓 FREE'
    elif model.pricing_input > 0:
        price_str = f'${model.pricing_input:.2f}/M'
    else:
        price_str = ''
    name = model.id
    if len(name) > 40:
        name = name[:37] + '...'
    return f'{name:<40} {fmt_tokens(model.context_length):>6} {fmt_tokens(model.max_output):>6}  {price_str}'
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/provider_detector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/provider_detector.py`

**Module Overview**: 
```text
Provider detection and model name normalization.
```

## Global Presets & Variables
- `validate_provider_configuration` = `validate_provider_config`

## Dependencies & Imports
re, typing.Tuple, typing.Optional, urllib.parse.urlparse

## Feature Class: `ProviderDetector`
**Description:**
```text
Detect provider from base URL and normalize model names accordingly.
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize provider detector.

Args:
    base_url: API base URL (e.g., "https://openrouter.ai/api/v1")
```

**Parameters:** `self, base_url`
**Implementation:**
```python
def __init__(self, base_url: str):
    """
        Initialize provider detector.
        
        Args:
            base_url: API base URL (e.g., "https://openrouter.ai/api/v1")
        """
    self.base_url = base_url
    self.provider = self._detect_provider()
```

### Method: `_detect_provider`
**Logic & Purpose:**
```text
Detect provider from base URL.

Returns:
    Provider name ('openrouter', 'gemini', 'openai', 'azure', 'unknown')
```

**Parameters:** `self`
**Variables Used:** `parsed, hostname`
**Implementation:**
```python
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
            if any((pattern in hostname for pattern in patterns)):
                return provider
        return 'unknown'
    except Exception:
        return 'unknown'
```

### Method: `normalize_model_name`
**Logic & Purpose:**
```text
Normalize model name based on detected provider.

For OpenRouter: Ensures provider prefix (e.g., "google/gemini-2.0-flash")
For Direct APIs: Strips provider prefix (e.g., "gemini-2.0-flash")

Args:
    model_name: Original model name
    
Returns:
    Normalized model name for the provider
```

**Parameters:** `self, model_name`
**Implementation:**
```python
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
    elif self.provider == 'vibeproxy':
        return self._normalize_for_vibeproxy(model_name)
    elif self.provider == 'antigravity':
        return self._normalize_for_antigravity(model_name)
    elif self.provider == 'gemini':
        return self._normalize_for_gemini(model_name)
    elif self.provider == 'openai':
        return self._normalize_for_openai(model_name)
    else:
        return model_name
```

### Method: `_normalize_for_openrouter`
**Logic & Purpose:**
```text
Normalize model name for OpenRouter.

OpenRouter requires provider prefixes like:
- google/gemini-2.0-flash-exp
- anthropic/claude-opus-4
- openai/gpt-4o

Args:
    model_name: Original model name
    
Returns:
    Model name with provider prefix
```

**Parameters:** `self, model_name`
**Implementation:**
```python
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
    if '/' in model_name:
        return model_name
    if model_name.startswith('gemini-'):
        return f'google/{model_name}'
    elif model_name.startswith('claude-'):
        return f'anthropic/{model_name}'
    elif model_name.startswith('gpt-') or model_name.startswith('o1-') or model_name.startswith('o3-'):
        return f'openai/{model_name}'
    elif model_name.startswith('llama-'):
        return f'meta-llama/{model_name}'
    else:
        return model_name
```

### Method: `_normalize_for_gemini`
**Logic & Purpose:**
```text
Normalize model name for direct Gemini API.

Gemini API expects model names without provider prefix:
- gemini-2.0-flash-exp (not google/gemini-2.0-flash-exp)

Args:
    model_name: Original model name
    
Returns:
    Model name without provider prefix
```

**Parameters:** `self, model_name`
**Implementation:**
```python
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
    if '/' in model_name:
        return model_name.split('/', 1)[1]
    return model_name
```

### Method: `_normalize_for_openai`
**Logic & Purpose:**
```text
Normalize model name for OpenAI API.

OpenAI API expects model names without provider prefix:
- gpt-4o (not openai/gpt-4o)

Args:
    model_name: Original model name

Returns:
    Model name without provider prefix
```

**Parameters:** `self, model_name`
**Implementation:**
```python
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
    if '/' in model_name:
        return model_name.split('/', 1)[1]
    return model_name
```

### Method: `_normalize_for_vibeproxy`
**Logic & Purpose:**
```text
Normalize model name for VibeProxy (CLIProxyAPI).

VibeProxy exposes models dynamically via its /v1/models endpoint.
Model names change across upgrades, so we do NOT hardcode any mappings.
The .env BIG_MODEL / MIDDLE_MODEL / SMALL_MODEL values should match
exactly what CLIProxyAPI reports in /v1/models.

Args:
    model_name: Original model name

Returns:
    Model name for VibeProxy (passthrough with prefix stripping)
```

**Parameters:** `self, model_name`
**Variables Used:** `model_name`
**Implementation:**
```python
def _normalize_for_vibeproxy(self, model_name: str) -> str:
    """
        Normalize model name for VibeProxy (CLIProxyAPI).

        VibeProxy exposes models dynamically via its /v1/models endpoint.
        Model names change across upgrades, so we do NOT hardcode any mappings.
        The .env BIG_MODEL / MIDDLE_MODEL / SMALL_MODEL values should match
        exactly what CLIProxyAPI reports in /v1/models.

        Args:
            model_name: Original model name

        Returns:
            Model name for VibeProxy (passthrough with prefix stripping)
        """
    if '/' in model_name:
        model_name = model_name.split('/', 1)[1]
    return model_name
```

### Method: `_normalize_for_antigravity`
**Logic & Purpose:**
```text
Normalize model name for Antigravity API.

Model names are dynamic and should match what the Antigravity
backend reports. No hardcoded mappings.

Args:
    model_name: Original model name

Returns:
    Model name for Antigravity (passthrough with prefix stripping)
```

**Parameters:** `self, model_name`
**Variables Used:** `model_name`
**Implementation:**
```python
def _normalize_for_antigravity(self, model_name: str) -> str:
    """
        Normalize model name for Antigravity API.

        Model names are dynamic and should match what the Antigravity
        backend reports. No hardcoded mappings.

        Args:
            model_name: Original model name

        Returns:
            Model name for Antigravity (passthrough with prefix stripping)
        """
    if '/' in model_name:
        model_name = model_name.split('/', 1)[1]
    return model_name
```

### Method: `get_provider_info`
**Logic & Purpose:**
```text
Get provider information.

Returns:
    Dictionary with provider details
```

**Parameters:** `self`
**Implementation:**
```python
def get_provider_info(self) -> dict:
    """
        Get provider information.
        
        Returns:
            Dictionary with provider details
        """
    return {'provider': self.provider, 'base_url': self.base_url, 'requires_prefix': self.provider == 'openrouter'}
```

---

## Feature Function: `detect_and_normalize`
**Logic & Purpose:**
```text
Convenience function to detect provider and normalize model name.

Args:
    base_url: API base URL
    model_name: Original model name
    
Returns:
    Tuple of (normalized_model_name, provider_info)
```

**Parameters:** `base_url, model_name`
**Variables Used:** `info, detector, normalized`
**Implementation:**
```python
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
    return (normalized, info)
```

---

## Feature Function: `validate_provider_config`
**Logic & Purpose:**
```text
Validate provider configuration.

Args:
    config: Configuration object
    
Returns:
    True if valid, False otherwise
```

**Parameters:** `config`
**Implementation:**
```python
def validate_provider_config(config) -> bool:
    """
    Validate provider configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        True if valid, False otherwise
    """
    if not config.openai_api_key and (not config.openai_base_url):
        return False
    if 'anthropic' in config.openai_base_url:
        print('⚠️  Warning: Base URL looks like Anthropic API. This proxy is for OpenAI-compatible providers.')
    return True
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/model_ranker.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/model_ranker.py`

**Module Overview**: 
```text
AI-Powered Model Ranker with Web Search

Uses LLM with tool calls (web search via Exa) to rank free models by coding capability.
The LLM can search for current benchmarks, community feedback, and model comparisons.

Configuration:
    RANKER_MODEL: LLM model for ranking (default: kwaicoder/kwaicoder-ds-v1)
    RANKER_USE_SEARCH: Enable web search (default: true)
    EXA_API_KEY: API key for Exa search (optional, enhances ranking accuracy)

Usage:
    python -m src.services.models.model_ranker --rank-free
    python -m src.services.models.model_ranker --top 10
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `MODELS_DIR` = `Path(__file__).parent.parent.parent / 'models'`
- `RANKINGS_PATH` = `MODELS_DIR / 'model_rankings.json'`
- `DEFAULT_FREE_MODELS` = `['kwaicoder/kwaicoder-ds-v1', 'deepseek/deepseek-chat-v3-0324:free', 'qwen/qwen3-235b-a22b:free', 'google/gemini-2.0-flash-exp:free', 'meta-llama/llama-3.3-70b-instruct:free', 'mistralai/mistral-7b-instruct:free']`
- `SEARCH_TOOLS` = `[{'type': 'function', 'function': {'name': 'web_search', 'description': 'Search the web for current information about LLM models, benchmarks, and coding performance. Use this to find recent benchmark scores, community feedback, and model comparisons.', 'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', 'description': "The search query. Be specific, e.g., 'DeepSeek V3 HumanEval benchmark score 2024' or 'best free LLM for Python coding'"}, 'num_results': {'type': 'integer', 'description': 'Number of results to return (1-5)', 'default': 3}}, 'required': ['query']}}}]`

## Dependencies & Imports
asyncio, json, logging, os, httpx, dataclasses.dataclass, dataclasses.asdict, dataclasses.field, typing.Dict, typing.List, typing.Optional, typing.Any, datetime.datetime, pathlib.Path

## Feature Class: `ModelRanking`
**Description:**
```text
Ranking for a model based on coding capability.
```

---

## Feature Function: `get_ranker_model`
**Logic & Purpose:**
```text
Get the model to use for ranking.
```

**Parameters:** ``
**Implementation:**
```python
def get_ranker_model() -> str:
    """Get the model to use for ranking."""
    return os.environ.get('RANKER_MODEL', os.environ.get('SCRAPER_MODEL', 'kwaicoder/kwaicoder-ds-v1'))
```

---

## Feature Function: `get_ranker_api_key`
**Logic & Purpose:**
```text
Get API key for ranker.
```

**Parameters:** ``
**Implementation:**
```python
def get_ranker_api_key() -> Optional[str]:
    """Get API key for ranker."""
    return os.environ.get('RANKER_API_KEY') or os.environ.get('SCRAPER_API_KEY') or os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('PROVIDER_API_KEY')
```

---

## Feature Function: `get_exa_api_key`
**Logic & Purpose:**
```text
Get Exa API key for web search.
```

**Parameters:** ``
**Implementation:**
```python
def get_exa_api_key() -> Optional[str]:
    """Get Exa API key for web search."""
    return os.environ.get('EXA_API_KEY')
```

---

## Feature Function: `should_use_web_search`
**Logic & Purpose:**
```text
Check if web search should be used for ranking.
```

**Parameters:** ``
**Implementation:**
```python
def should_use_web_search() -> bool:
    """Check if web search should be used for ranking."""
    if os.environ.get('RANKER_USE_SEARCH', 'true').lower() != 'true':
        return False
    return get_exa_api_key() is not None
```

---

## Feature Function: `exa_search`
**Logic & Purpose:**
```text
Search using Exa API for current model information.

Returns list of search results with title, url, and snippet.
```

**Parameters:** `query, num_results`
**Variables Used:** `results, data, response, api_key`
**Implementation:**
```python
async def exa_search(query: str, num_results: int=3) -> List[Dict]:
    """
    Search using Exa API for current model information.
    
    Returns list of search results with title, url, and snippet.
    """
    api_key = get_exa_api_key()
    if not api_key:
        return []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post('https://api.exa.ai/search', headers={'x-api-key': api_key, 'Content-Type': 'application/json'}, json={'query': query, 'numResults': min(num_results, 5), 'useAutoprompt': True, 'type': 'neural', 'contents': {'text': {'maxCharacters': 500}}})
            if response.status_code != 200:
                logger.warning(f'Exa search failed: {response.status_code}')
                return []
            data = response.json()
            results = []
            for r in data.get('results', []):
                results.append({'title': r.get('title', ''), 'url': r.get('url', ''), 'snippet': r.get('text', '')[:300]})
            return results
        except Exception as e:
            logger.error(f'Exa search error: {e}')
            return []
```

---

## Feature Function: `execute_tool_call`
**Logic & Purpose:**
```text
Execute a tool call and return the result.
```

**Parameters:** `tool_name, arguments`
**Variables Used:** `results, formatted, query, num_results`
**Implementation:**
```python
async def execute_tool_call(tool_name: str, arguments: Dict) -> str:
    """Execute a tool call and return the result."""
    if tool_name == 'web_search':
        query = arguments.get('query', '')
        num_results = arguments.get('num_results', 3)
        results = await exa_search(query, num_results)
        if not results:
            return 'No search results found. Please proceed with your existing knowledge.'
        formatted = []
        for r in results:
            formatted.append(f"**{r['title']}**\n{r['url']}\n{r['snippet']}\n")
        return '\n---\n'.join(formatted)
    return f'Unknown tool: {tool_name}'
```

---

## Feature Function: `fetch_free_models_from_openrouter`
**Logic & Purpose:**
```text
Fetch list of free models from OpenRouter API.
```

**Parameters:** ``
**Variables Used:** `completion_price, data, api_key, headers, pricing, prompt_price, models, response, free_models`
**Implementation:**
```python
async def fetch_free_models_from_openrouter() -> List[Dict]:
    """Fetch list of free models from OpenRouter API."""
    api_key = get_ranker_api_key()
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        try:
            response = await client.get('https://openrouter.ai/api/v1/models', headers=headers)
            if response.status_code != 200:
                logger.warning(f'Failed to fetch models: HTTP {response.status_code}')
                return []
            data = response.json()
            models = data.get('data', [])
            free_models = []
            for model in models:
                pricing = model.get('pricing', {})
                prompt_price = float(pricing.get('prompt', 0))
                completion_price = float(pricing.get('completion', 0))
                if prompt_price == 0 and completion_price == 0:
                    free_models.append({'id': model.get('id'), 'name': model.get('name'), 'context_length': model.get('context_length', 0), 'created': model.get('created', 0), 'description': model.get('description', '')[:200]})
            return free_models
        except Exception as e:
            logger.error(f'Error fetching models: {e}')
            return []
```

---

## Feature Function: `rank_models_with_llm`
**Logic & Purpose:**
```text
Use LLM with tool calls to rank models by coding capability.

If web search is enabled, the LLM can search for:
- Current benchmark scores (HumanEval, MBPP, etc.)
- Community feedback and reviews
- Model comparisons and rankings
```

**Parameters:** `models, use_web_search`
**Variables Used:** `rankings_data, func, arguments, max_tool_iterations, request_body, json_str, search_count, ranking, sources_used, messages, json_start, rankings, data, message, result, tool_calls, json_end, api_key, system_prompt, tool_name, choice, response, content, ranker_model, user_prompt, model_summary`
**Implementation:**
```python
async def rank_models_with_llm(models: List[Dict], use_web_search: bool=True) -> List[ModelRanking]:
    """
    Use LLM with tool calls to rank models by coding capability.
    
    If web search is enabled, the LLM can search for:
    - Current benchmark scores (HumanEval, MBPP, etc.)
    - Community feedback and reviews
    - Model comparisons and rankings
    """
    api_key = get_ranker_api_key()
    ranker_model = get_ranker_model()
    if not api_key:
        logger.warning('No API key available for ranking')
        return []
    model_summary = '\n'.join([f"- {m['id']}: {m.get('name', 'Unknown')} (ctx: {m.get('context_length', 0):,})" for m in models[:30]])
    system_prompt = 'You are an expert at evaluating LLM models for coding tasks.\n\n## YOUR MISSION\nRank the provided free models by their **coding capability** using factual data.\n\n## TOOLS AVAILABLE\nYou have access to a `web_search` tool. USE IT to find:\n1. Recent benchmark scores (HumanEval, MBPP, SWE-Bench, etc.)\n2. Community comparisons and reviews\n3. Official model release announcements with capabilities\n\n## EVALUATION CRITERIA (in order of importance)\n1. **Coding benchmarks**: HumanEval pass@1, MBPP, SWE-Bench scores\n2. **Architecture quality**: Parameter count, training data, specialization\n3. **Context length**: Larger = better for codebases\n4. **Community feedback**: Real-world coding performance\n5. **Recency**: Newer models often perform better\n\n## EVALUATION FOCUS\nModels should be good at:\n- Code generation (Python, JavaScript, TypeScript priority)\n- Code completion and refactoring\n- Debugging and error analysis\n- Understanding large codebases\n\n## PROCESS\n1. First, search for benchmark data on the most promising models\n2. Cross-reference with community feedback\n3. Produce your final rankings\n\n## OUTPUT FORMAT\nAfter gathering data, return ONLY a JSON array:\n```json\n[\n  {\n    "model_id": "provider/model-name",\n    "rank": 1,\n    "coding_score": 85,\n    "strengths": ["high HumanEval score", "good at Python"],\n    "weaknesses": ["slower inference"],\n    "best_for": ["python", "debugging", "refactoring"],\n    "reasoning": "Brief explanation with data sources"\n  }\n]\n```\n\nRank the top 10-15 models. Only include models from the provided list.'
    user_prompt = f'Please rank these FREE models for coding tasks:\n\n{model_summary}\n\nIMPORTANT: Use the web_search tool to find current benchmark data before ranking.\nSearch for terms like:\n- "[model name] HumanEval benchmark"\n- "[model name] coding performance"\n- "best free LLM for coding 2024"\n\nAfter researching, return your rankings as a JSON array.'
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
    max_tool_iterations = 5
    search_count = 0
    sources_used = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for iteration in range(max_tool_iterations):
            try:
                request_body = {'model': ranker_model, 'messages': messages, 'temperature': 0.3, 'max_tokens': 4000}
                if use_web_search and should_use_web_search() and (search_count < 3):
                    request_body['tools'] = SEARCH_TOOLS
                    request_body['tool_choice'] = 'auto'
                response = await client.post('https://openrouter.ai/api/v1/chat/completions', headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}, json=request_body)
                if response.status_code != 200:
                    logger.error(f'Ranking API error: {response.status_code} - {response.text}')
                    break
                data = response.json()
                choice = data.get('choices', [{}])[0]
                message = choice.get('message', {})
                tool_calls = message.get('tool_calls', [])
                if tool_calls:
                    messages.append(message)
                    for tool_call in tool_calls:
                        func = tool_call.get('function', {})
                        tool_name = func.get('name')
                        try:
                            arguments = json.loads(func.get('arguments', '{}'))
                        except json.JSONDecodeError:
                            arguments = {}
                        print(f"   🔍 Searching: {arguments.get('query', '')[:50]}...")
                        result = await execute_tool_call(tool_name, arguments)
                        search_count += 1
                        if 'http' in result:
                            for line in result.split('\n'):
                                if line.startswith('http'):
                                    sources_used.append(line.strip())
                        messages.append({'role': 'tool', 'tool_call_id': tool_call.get('id'), 'content': result})
                    continue
                content = message.get('content', '')
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    rankings_data = json.loads(json_str)
                    rankings = []
                    for item in rankings_data:
                        ranking = ModelRanking(model_id=item.get('model_id', ''), rank=item.get('rank', 99), coding_score=item.get('coding_score', 0), strengths=item.get('strengths', []), weaknesses=item.get('weaknesses', []), best_for=item.get('best_for', []), reasoning=item.get('reasoning', ''), sources=sources_used[:5], ranked_at=datetime.now().isoformat())
                        rankings.append(ranking)
                    return sorted(rankings, key=lambda r: r.rank)
                else:
                    logger.error('Could not parse JSON from LLM response')
                    logger.debug(f'Response content: {content[:500]}')
                    break
            except json.JSONDecodeError as e:
                logger.error(f'JSON parse error: {e}')
                break
            except Exception as e:
                logger.error(f'Ranking error: {e}')
                break
    return []
```

---

## Feature Function: `save_rankings`
**Logic & Purpose:**
```text
Save rankings to local database.
```

**Parameters:** `rankings`
**Variables Used:** `data`
**Implementation:**
```python
def save_rankings(rankings: List[ModelRanking]):
    """Save rankings to local database."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    data = {'updated_at': datetime.now().isoformat(), 'ranker_model': get_ranker_model(), 'web_search_used': should_use_web_search(), 'rankings': [asdict(r) for r in rankings]}
    with open(RANKINGS_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f'Saved {len(rankings)} rankings to {RANKINGS_PATH}')
```

---

## Feature Function: `load_rankings`
**Logic & Purpose:**
```text
Load rankings from local database.
```

**Parameters:** ``
**Variables Used:** `rankings, data`
**Implementation:**
```python
def load_rankings() -> List[ModelRanking]:
    """Load rankings from local database."""
    if not RANKINGS_PATH.exists():
        return []
    try:
        with open(RANKINGS_PATH, 'r') as f:
            data = json.load(f)
        rankings = []
        for item in data.get('rankings', []):
            if 'sources' not in item:
                item['sources'] = []
            rankings.append(ModelRanking(**item))
        return sorted(rankings, key=lambda r: r.rank)
    except Exception as e:
        logger.error(f'Error loading rankings: {e}')
        return []
```

---

## Feature Function: `get_top_coding_models`
**Logic & Purpose:**
```text
Get top N coding models from saved rankings.
```

**Parameters:** `n`
**Variables Used:** `rankings`
**Implementation:**
```python
def get_top_coding_models(n: int=5) -> List[ModelRanking]:
    """Get top N coding models from saved rankings."""
    rankings = load_rankings()
    return rankings[:n]
```

---

## Feature Function: `update_rankings`
**Logic & Purpose:**
```text
Fetch free models and update rankings.
```

**Parameters:** ``
**Variables Used:** `exa_key, free_models, strengths, rankings`
**Implementation:**
```python
async def update_rankings():
    """Fetch free models and update rankings."""
    print('🔄 Fetching free models from OpenRouter...')
    free_models = await fetch_free_models_from_openrouter()
    if not free_models:
        print('❌ No free models found. Using defaults...')
        free_models = [{'id': m, 'name': m.split('/')[-1]} for m in DEFAULT_FREE_MODELS]
    print(f'📊 Found {len(free_models)} free models')
    print(f'🤖 Ranking with: {get_ranker_model()}')
    if should_use_web_search():
        print('🌐 Web search ENABLED (Exa API)')
    else:
        exa_key = get_exa_api_key()
        if not exa_key:
            print('⚠️  Web search disabled (set EXA_API_KEY to enable)')
        else:
            print('⚠️  Web search disabled (set RANKER_USE_SEARCH=true to enable)')
    print('\n🔍 Analyzing models...')
    rankings = await rank_models_with_llm(free_models)
    if rankings:
        save_rankings(rankings)
        print(f'\n✅ Ranked {len(rankings)} models for coding\n')
        print('Top models for coding:')
        for r in rankings[:10]:
            strengths = ', '.join(r.strengths[:2]) if r.strengths else '—'
            print(f'  {r.rank:2}. {r.model_id:<45} Score: {r.coding_score:<3} | {strengths}')
        if rankings[0].sources:
            print(f'\n📚 Sources used: {len(rankings[0].sources)}')
    else:
        print('❌ Failed to generate rankings')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/catalog_sync.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/catalog_sync.py`

**Module Overview**: 
```text
Model Catalog Sync Script

Syncs model-scraper output into the main proxy's model catalog.
Can be run manually or scheduled weekly.

Usage:
    python -m src.services.models.catalog_sync          # Sync from scraper
    python -m src.services.models.catalog_sync --force # Force refresh
    python -m src.services.models.catalog_sync --show  # Show current catalog
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent.parent`
- `MODELS_DIR` = `PROJECT_ROOT / 'models'`
- `SCRAPER_DIR` = `PROJECT_ROOT / 'model-scraper'`
- `SCRAPER_DATA_DIR` = `SCRAPER_DIR / 'data'`
- `SCRAPER_LEADERBOARD` = `SCRAPER_DATA_DIR / 'leaderboard.json'`
- `SCRAPER_MODELS` = `SCRAPER_DATA_DIR / 'models.json'`
- `CATALOG_PATH` = `MODELS_DIR / 'model_catalog.json'`

## Dependencies & Imports
argparse, json, logging, subprocess, sys, datetime.datetime, datetime.timezone, pathlib.Path, typing.Optional

## Feature Function: `sync_from_scraper`
**Logic & Purpose:**
```text
Sync model catalog from scraper output.
```

**Parameters:** ``
**Variables Used:** `catalog, model_id, full_spec, category_models, leaderboard, models_data, spec`
**Implementation:**
```python
def sync_from_scraper() -> bool:
    """Sync model catalog from scraper output."""
    logger.info('Syncing model catalog from scraper...')
    if not SCRAPER_LEADERBOARD.exists():
        logger.warning(f'Scraper output not found at {SCRAPER_LEADERBOARD}')
        return False
    try:
        with open(SCRAPER_LEADERBOARD) as f:
            leaderboard = json.load(f)
        models_data = {}
        if SCRAPER_MODELS.exists():
            with open(SCRAPER_MODELS) as f:
                models_data = json.load(f)
        catalog = {'generated_at': leaderboard.get('generated_at', datetime.now(timezone.utc).isoformat()), 'models': {}, 'all_models': {}}
        for category in ['smartest', 'coding', 'free', 'value']:
            category_models = leaderboard.get(category, [])
            catalog['models'][category] = []
            for rank, model in enumerate(category_models, 1):
                model_id = model.get('id', '')
                full_spec = {}
                if models_data:
                    for m in models_data:
                        if m.get('id') == model_id:
                            full_spec = m
                            break
                spec = {'id': model_id, 'name': model.get('name', model_id), 'provider': model_id.split('/')[0] if '/' in model_id else 'unknown', 'context_length': full_spec.get('context_length') or model.get('context_length') or 128000, 'max_output': full_spec.get('max_output_tokens') or full_spec.get('max_output') or 4096, 'price_per_1m_input': full_spec.get('price_per_1m_input', 0.0), 'price_per_1m_output': full_spec.get('price_per_1m_output', 0.0), 'throughput_tps': model.get('throughput_tps'), 'intelligence_score': model.get('intelligence_score'), 'is_free': ':free' in model_id.lower(), 'category': category, 'rank': rank}
                catalog['models'][category].append(spec)
                catalog['all_models'][model_id] = spec
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(CATALOG_PATH, 'w') as f:
            json.dump(catalog, f, indent=2)
        logger.info(f'Saved model catalog to {CATALOG_PATH}')
        logger.info(f"Catalog contains {len(catalog['all_models'])} models across {len(catalog['models'])} categories")
        return True
    except Exception as e:
        logger.error(f'Error syncing catalog: {e}')
        return False
```

---

## Feature Function: `show_catalog`
**Logic & Purpose:**
```text
Display current model catalog.
```

**Parameters:** ``
**Variables Used:** `catalog, free_badge, ctx, models, ctx_str`
**Implementation:**
```python
def show_catalog():
    """Display current model catalog."""
    if not CATALOG_PATH.exists():
        print('No model catalog found. Run with --sync to create one.')
        return
    with open(CATALOG_PATH) as f:
        catalog = json.load(f)
    print(f"\n📦 Model Catalog (generated: {catalog.get('generated_at', 'unknown')})\n")
    for category in ['free', 'smartest', 'coding', 'value']:
        models = catalog.get('models', {}).get(category, [])
        print(f'━━━ {category.upper()} ━━━')
        for m in models[:5]:
            free_badge = ' 🆓' if m.get('is_free') else ''
            ctx = m.get('context_length', 0)
            ctx_str = f'{ctx / 1000:.0f}k' if ctx else '?'
            print(f"  {m.get('name', m['id'])} [{ctx_str} ctx]{free_badge}")
        print()
```

---

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `args, parser`
**Implementation:**
```python
def main():
    parser = argparse.ArgumentParser(description='Model Catalog Sync Tool')
    parser.add_argument('--sync', action='store_true', help='Sync from scraper')
    parser.add_argument('--run-scraper', action='store_true', help='Run scraper then sync')
    parser.add_argument('--show', action='store_true', help='Show current catalog')
    parser.add_argument('--force', action='store_true', help='Force refresh')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if args.show:
        show_catalog()
        return
    if args.run_scraper or args.sync:
        if args.run_scraper:
            if not run_scraper():
                logger.error('Failed to run scraper')
                sys.exit(1)
        if not sync_from_scraper():
            logger.error('Failed to sync catalog')
            sys.exit(1)
        show_catalog()
    else:
        parser.print_help()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/openrouter_enricher.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/openrouter_enricher.py`

**Module Overview**: 
```text
OpenRouter Model Enricher

Parses the OpenRouter API response and extracts all useful model metadata
into a structured JSON format for use in TUI and Web UI model selectors.
```

## Dependencies & Imports
json, os, pathlib.Path, typing.Dict, typing.List, typing.Any, typing.Optional, datetime.datetime

## Feature Function: `parse_models_file`
**Logic & Purpose:**
```text
Parse the OpenRouter models API response.
```

**Parameters:** `filepath`
**Variables Used:** `data`
**Implementation:**
```python
def parse_models_file(filepath: str) -> List[Dict[str, Any]]:
    """Parse the OpenRouter models API response."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError('Unexpected models file format')
```

---

## Feature Function: `extract_provider`
**Logic & Purpose:**
```text
Extract provider name from model ID.
```

**Parameters:** `model_id`
**Implementation:**
```python
def extract_provider(model_id: str) -> str:
    """Extract provider name from model ID."""
    if '/' in model_id:
        return model_id.split('/')[0]
    return 'unknown'
```

---

## Feature Function: `supports_feature`
**Logic & Purpose:**
```text
Check if model supports a specific feature.
```

**Parameters:** `params, feature`
**Implementation:**
```python
def supports_feature(params: List[str], feature: str) -> bool:
    """Check if model supports a specific feature."""
    return feature in params if params else False
```

---

## Feature Function: `enrich_model`
**Logic & Purpose:**
```text
Transform raw OpenRouter model data into enriched format.

Extracts all useful fields for display in model selectors.
```

**Parameters:** `model`
**Variables Used:** `model_id, supports_structured, architecture, pricing, top_provider, supports_vision, supports_audio, is_free, supported_params, output_price, supports_tools, supports_files, supports_reasoning, input_modalities, output_modalities, input_price`
**Implementation:**
```python
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

    def parse_price(price_str: str) -> float:
        try:
            return float(price_str) * 1000000 if price_str else 0.0
        except (ValueError, TypeError):
            return 0.0
    input_price = parse_price(pricing.get('prompt', '0'))
    output_price = parse_price(pricing.get('completion', '0'))
    input_modalities = architecture.get('input_modalities', ['text'])
    output_modalities = architecture.get('output_modalities', ['text'])
    supports_vision = any((m in input_modalities for m in ['image', 'video']))
    supports_audio = 'audio' in input_modalities
    supports_files = 'file' in input_modalities
    supports_reasoning = supports_feature(supported_params, 'reasoning') or supports_feature(supported_params, 'include_reasoning')
    supports_tools = supports_feature(supported_params, 'tools')
    supports_structured = supports_feature(supported_params, 'structured_outputs')
    is_free = input_price == 0 and output_price == 0 or model_id.endswith(':free')
    return {'id': model_id, 'name': model.get('name', model_id), 'provider': extract_provider(model_id), 'canonical_slug': model.get('canonical_slug', ''), 'hugging_face_id': model.get('hugging_face_id', ''), 'description': model.get('description', ''), 'context_length': model.get('context_length', 0), 'max_completion_tokens': top_provider.get('max_completion_tokens', 0) or 0, 'modality': architecture.get('modality', 'text->text'), 'input_modalities': input_modalities, 'output_modalities': output_modalities, 'tokenizer': architecture.get('tokenizer', 'Unknown'), 'supports_reasoning': supports_reasoning, 'supports_tools': supports_tools, 'supports_vision': supports_vision, 'supports_audio': supports_audio, 'supports_files': supports_files, 'supports_structured_output': supports_structured, 'pricing': {'input_per_million': round(input_price, 4), 'output_per_million': round(output_price, 4), 'is_free': is_free}, 'is_moderated': top_provider.get('is_moderated', False), 'supported_parameters': supported_params, 'created': model.get('created', 0)}
```

---

## Feature Function: `enrich_all_models`
**Logic & Purpose:**
```text
Process all models and output enriched JSON.

Returns summary statistics.
```

**Parameters:** `input_file, output_file`
**Variables Used:** `enriched, stats, output, models, provider, enriched_model`
**Implementation:**
```python
def enrich_all_models(input_file: str, output_file: str) -> Dict[str, Any]:
    """
    Process all models and output enriched JSON.
    
    Returns summary statistics.
    """
    print(f'📖 Reading models from: {input_file}')
    models = parse_models_file(input_file)
    print(f'   Found {len(models)} models')
    enriched = []
    stats = {'total': len(models), 'free': 0, 'reasoning': 0, 'vision': 0, 'tools': 0, 'by_provider': {}}
    for model in models:
        enriched_model = enrich_model(model)
        enriched.append(enriched_model)
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
    enriched.sort(key=lambda m: (m['provider'], m['name']))
    output = {'generated_at': datetime.now().isoformat(), 'source': 'OpenRouter API', 'stats': stats, 'models': enriched}
    print(f'💾 Writing enriched data to: {output_file}')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f'\n✅ Enrichment complete!')
    print(f"   Total models: {stats['total']}")
    print(f"   Free models: {stats['free']}")
    print(f"   Reasoning-capable: {stats['reasoning']}")
    print(f"   Vision-capable: {stats['vision']}")
    print(f"   Tool-use capable: {stats['tools']}")
    print(f"   Providers: {len(stats['by_provider'])}")
    return stats
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main entry point.
```

**Parameters:** ``
**Variables Used:** `output_file, input_file, project_root`
**Implementation:**
```python
def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent.parent
    input_file = project_root / 'models.txt'
    output_file = project_root / 'data' / 'openrouter_models_enriched.json'
    if not input_file.exists():
        print(f'❌ Input file not found: {input_file}')
        print('   Run: curl https://openrouter.ai/api/v1/models > models.txt')
        return
    output_file.parent.mkdir(parents=True, exist_ok=True)
    enrich_all_models(str(input_file), str(output_file))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/openrouter_rankings.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/openrouter_rankings.py`

**Module Overview**: 
```text
OpenRouter Rankings Scraper

Scrapes OpenRouter's official rankings page to get:
- Overall leaderboard (token usage)
- Programming language rankings
- Tool call rankings

Uses this data to filter "top" models for the model selector.

Usage:
    python -m src.services.models.openrouter_rankings --scrape
    python -m src.services.models.openrouter_rankings --show
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `MODELS_DIR` = `Path(__file__).parent.parent.parent / 'models'`
- `RANKINGS_DB_PATH` = `MODELS_DIR / 'openrouter_rankings.json'`

## Dependencies & Imports
asyncio, json, logging, os, dataclasses.dataclass, dataclasses.asdict, dataclasses.field, datetime.datetime, pathlib.Path, typing.Dict, typing.List, typing.Optional, typing.Any

## Feature Class: `RankedModel`
**Description:**
```text
A model from OpenRouter rankings.
```

---

## Feature Class: `OpenRouterRankings`
**Description:**
```text
OpenRouter rankings database.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self._data: Dict[str, List[Dict]] = {'overall': [], 'programming': [], 'tool_calls': [], 'updated_at': ''}
    self._load()
```

### Method: `_load`
**Logic & Purpose:**
```text
Load rankings from file.
```

**Parameters:** `self`
**Implementation:**
```python
def _load(self):
    """Load rankings from file."""
    if RANKINGS_DB_PATH.exists():
        try:
            with open(RANKINGS_DB_PATH, 'r') as f:
                self._data = json.load(f)
            logger.info(f'Loaded rankings from {RANKINGS_DB_PATH}')
        except Exception as e:
            logger.warning(f'Failed to load rankings: {e}')
```

### Method: `save`
**Logic & Purpose:**
```text
Save rankings to file.
```

**Parameters:** `self`
**Implementation:**
```python
def save(self):
    """Save rankings to file."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    self._data['updated_at'] = datetime.now().isoformat()
    with open(RANKINGS_DB_PATH, 'w') as f:
        json.dump(self._data, f, indent=2)
    logger.info(f'Saved rankings to {RANKINGS_DB_PATH}')
```

### Method: `set_rankings`
**Logic & Purpose:**
```text
Set rankings for a category.
```

**Parameters:** `self, category, models`
**Implementation:**
```python
def set_rankings(self, category: str, models: List[RankedModel]):
    """Set rankings for a category."""
    self._data[category] = [asdict(m) for m in models]
```

### Method: `get_top_models`
**Logic & Purpose:**
```text
Get top N model IDs for a category.
```

**Parameters:** `self, category, n`
**Variables Used:** `rankings`
**Implementation:**
```python
def get_top_models(self, category: str='overall', n: int=20) -> List[str]:
    """Get top N model IDs for a category."""
    rankings = self._data.get(category, [])
    return [r['model_id'] for r in rankings[:n]]
```

### Method: `is_top_model`
**Logic & Purpose:**
```text
Check if model is in top rankings.
```

**Parameters:** `self, model_id, categories`
**Variables Used:** `categories`
**Implementation:**
```python
def is_top_model(self, model_id: str, categories: List[str]=None) -> bool:
    """Check if model is in top rankings."""
    if categories is None:
        categories = ['overall', 'programming', 'tool_calls']
    for cat in categories:
        if model_id in self.get_top_models(cat, 30):
            return True
    return False
```

### Method: `get_model_rank`
**Logic & Purpose:**
```text
Get rank for a specific model.
```

**Parameters:** `self, model_id, category`
**Variables Used:** `rankings`
**Implementation:**
```python
def get_model_rank(self, model_id: str, category: str='overall') -> Optional[int]:
    """Get rank for a specific model."""
    rankings = self._data.get(category, [])
    for r in rankings:
        if r['model_id'] == model_id:
            return r['rank']
    return None
```

---

## Feature Function: `scrape_rankings_with_playwright`
**Logic & Purpose:**
```text
Scrape OpenRouter rankings page using Playwright.

Returns rankings for overall, programming, and tool_calls categories.
```

**Parameters:** ``
**Variables Used:** `seen, page, results, text, found_models, section_text, rank, excluded_prefixes, valid_models, content, section_models, model_pattern, sections, browser`
**Implementation:**
```python
async def scrape_rankings_with_playwright() -> Dict[str, List[RankedModel]]:
    """
    Scrape OpenRouter rankings page using Playwright.
    
    Returns rankings for overall, programming, and tool_calls categories.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error('Playwright not installed. Run: pip install playwright && playwright install')
        return {}
    results = {'overall': [], 'programming': [], 'tool_calls': []}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print('🔄 Navigating to OpenRouter rankings...')
            await page.goto('https://openrouter.ai/rankings', wait_until='networkidle')
            await asyncio.sleep(3)
            content = await page.content()
            text = await page.inner_text('body')
            import re
            model_pattern = '([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+(?::[a-zA-Z0-9_-]+)?)'
            found_models = re.findall(model_pattern, text)
            excluded_prefixes = ['http', 'www', 'openrouter', 'api', 'docs']
            valid_models = []
            for m in found_models:
                if not any((m.lower().startswith(ex) for ex in excluded_prefixes)):
                    if m not in valid_models:
                        valid_models.append(m)
            print(f'📊 Found {len(valid_models)} model references')
            sections = [('#market-share', 'overall'), ('#programming-languages', 'programming'), ('#tools', 'tool_calls')]
            for selector, category in sections:
                try:
                    await page.goto(f'https://openrouter.ai/rankings{selector}', wait_until='networkidle')
                    await asyncio.sleep(2)
                    section_text = await page.inner_text('body')
                    section_models = re.findall(model_pattern, section_text)
                    rank = 1
                    seen = set()
                    for m in section_models:
                        if m not in seen and (not any((m.lower().startswith(ex) for ex in excluded_prefixes))):
                            seen.add(m)
                            results[category].append(RankedModel(model_id=m, rank=rank, category=category, is_free=':free' in m.lower(), scraped_at=datetime.now().isoformat()))
                            rank += 1
                            if rank > 30:
                                break
                    print(f'   {category}: {len(results[category])} models')
                except Exception as e:
                    logger.debug(f'Error scraping {category}: {e}')
            if len(results['overall']) < 5:
                print('⚠️  Limited data from scraping, using known top models...')
                results = _get_fallback_rankings()
        except Exception as e:
            logger.error(f'Scraping error: {e}')
            results = _get_fallback_rankings()
        finally:
            await browser.close()
    return results
```

---

## Feature Function: `_get_fallback_rankings`
**Logic & Purpose:**
```text
Fallback rankings based on known popular models.
```

**Parameters:** ``
**Variables Used:** `now, results, tool_calls, overall, programming`
**Implementation:**
```python
def _get_fallback_rankings() -> Dict[str, List[RankedModel]]:
    """Fallback rankings based on known popular models."""
    now = datetime.now().isoformat()
    overall = ['anthropic/claude-3.5-sonnet', 'anthropic/claude-3.5-haiku', 'openai/gpt-4o', 'openai/gpt-4o-mini', 'google/gemini-2.0-flash-exp:free', 'google/gemini-2.5-flash-preview-05-20', 'deepseek/deepseek-chat-v3-0324:free', 'meta-llama/llama-3.3-70b-instruct', 'qwen/qwen-2.5-72b-instruct', 'anthropic/claude-3-opus', 'openai/o1-mini', 'openai/o3-mini', 'x-ai/grok-2-1212', 'mistralai/mistral-large', 'cohere/command-r-plus']
    programming = ['anthropic/claude-3.5-sonnet', 'deepseek/deepseek-chat-v3-0324:free', 'openai/gpt-4o', 'google/gemini-2.0-flash-exp:free', 'qwen/qwen-2.5-coder-32b-instruct', 'openai/o1-mini', 'meta-llama/codellama-70b-instruct', 'anthropic/claude-3.5-haiku', 'deepseek/deepseek-coder', 'kwaicoder/kwaicoder-ds-v1:free']
    tool_calls = ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'openai/gpt-4o-mini', 'google/gemini-2.0-flash-exp:free', 'anthropic/claude-3.5-haiku', 'deepseek/deepseek-chat-v3-0324:free', 'qwen/qwen-2.5-72b-instruct', 'meta-llama/llama-3.3-70b-instruct']
    results = {}
    for category, models in [('overall', overall), ('programming', programming), ('tool_calls', tool_calls)]:
        results[category] = [RankedModel(model_id=m, rank=i + 1, category=category, is_free=':free' in m.lower(), scraped_at=now) for i, m in enumerate(models)]
    return results
```

---

## Feature Function: `update_rankings`
**Logic & Purpose:**
```text
Scrape and update rankings database.
```

**Parameters:** ``
**Variables Used:** `db, rankings_data`
**Implementation:**
```python
async def update_rankings():
    """Scrape and update rankings database."""
    print('🔄 Scraping OpenRouter rankings...')
    rankings_data = await scrape_rankings_with_playwright()
    db = OpenRouterRankings()
    for category, models in rankings_data.items():
        if models:
            db.set_rankings(category, models)
    db.save()
    print(f'\n✅ Rankings updated!')
    print(f"   Overall: {len(rankings_data.get('overall', []))} models")
    print(f"   Programming: {len(rankings_data.get('programming', []))} models")
    print(f"   Tool Calls: {len(rankings_data.get('tool_calls', []))} models")
```

---

## Feature Function: `get_rankings`
**Logic & Purpose:**
```text
Get the rankings database.
```

**Parameters:** ``
**Implementation:**
```python
def get_rankings() -> OpenRouterRankings:
    """Get the rankings database."""
    return OpenRouterRankings()
```

---

## Feature Function: `filter_top_openrouter_models`
**Logic & Purpose:**
```text
Filter OpenRouter models to only include top-ranked ones.

Returns models that appear in any of the ranking categories.
```

**Parameters:** `models, include_top_overall, include_top_programming, include_top_tool_calls`
**Variables Used:** `top_overall, filtered, top_tool_calls, db, all_top, top_programming`
**Implementation:**
```python
def filter_top_openrouter_models(models: List[str], include_top_overall: int=20, include_top_programming: int=15, include_top_tool_calls: int=10) -> List[str]:
    """
    Filter OpenRouter models to only include top-ranked ones.
    
    Returns models that appear in any of the ranking categories.
    """
    db = OpenRouterRankings()
    top_overall = set(db.get_top_models('overall', include_top_overall))
    top_programming = set(db.get_top_models('programming', include_top_programming))
    top_tool_calls = set(db.get_top_models('tool_calls', include_top_tool_calls))
    all_top = top_overall | top_programming | top_tool_calls
    filtered = []
    for m in models:
        if m in all_top or ':free' in m.lower() or m.endswith(':free'):
            filtered.append(m)
    return filtered
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/benchmarking/model_benchmarks.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/benchmarking/model_benchmarks.py`

**Module Overview**: 
```text
Automated Model Benchmarking System

Tests models with standardized prompts to compare:
- Performance (latency, throughput)
- Quality (output correctness)
- Cost efficiency
- Reliability
```

## Global Presets & Variables
- `BENCHMARK_TESTS` = `load_benchmark_tests()`
- `model_benchmarker` = `ModelBenchmarker()`

## Dependencies & Imports
typing.Dict, typing.Any, typing.List, typing.Optional, datetime.datetime, asyncio, time, json, pathlib.Path, httpx, src.core.logging.logger

## Feature Class: `BenchmarkTest`
**Description:**
```text
A single benchmark test case
```

### Method: `__init__`
**Parameters:** `self, name, prompt, expected_keywords, category`
**Implementation:**
```python
def __init__(self, name: str, prompt: str, expected_keywords: List[str]=None, category: str='general'):
    self.name = name
    self.prompt = prompt
    self.expected_keywords = expected_keywords or []
    self.category = category
```

---

## Feature Function: `load_benchmark_tests`
**Logic & Purpose:**
```text
Load benchmark tests from JSON file
```

**Parameters:** ``
**Variables Used:** `tests, benchmarks_file, data`
**Implementation:**
```python
def load_benchmark_tests() -> List[BenchmarkTest]:
    """Load benchmark tests from JSON file"""
    try:
        benchmarks_file = Path('data/benchmarks.json')
        if not benchmarks_file.exists():
            return [BenchmarkTest(name='Simple Math', prompt='What is 123 + 456? Answer with just the number.', expected_keywords=['579'], category='reasoning'), BenchmarkTest(name='Code Generation', prompt='Write a Python function to calculate fibonacci number. Include only the code, no explanation.', expected_keywords=['def', 'fibonacci', 'return'], category='coding')]
        with open(benchmarks_file, 'r') as f:
            data = json.load(f)
        tests = []
        for item in data.get('tests', []):
            tests.append(BenchmarkTest(name=item['name'], prompt=item['prompt'], expected_keywords=item.get('expected_keywords', []), category=item.get('category', 'general')))
        return tests
    except Exception as e:
        logger.error(f'Failed to load benchmarks: {e}')
        return []
```

---

## Feature Class: `ModelBenchmarker`
**Description:**
```text
Runs benchmarks against models and records results
```

### Method: `__init__`
**Parameters:** `self, base_url, api_key`
**Implementation:**
```python
def __init__(self, base_url: str='http://localhost:8082', api_key: str='test'):
    self.base_url = base_url
    self.api_key = api_key
    self.results_dir = Path('benchmark_results')
    self.results_dir.mkdir(exist_ok=True)
```

### Method: `benchmark_model`
**Logic & Purpose:**
```text
Benchmark a single model.

Args:
    model_name: Name of the model to test
    tests: List of tests to run (defaults to BENCHMARK_TESTS)
    iterations: Number of times to run each test

Returns:
    Dictionary with benchmark results
```

**Parameters:** `self, model_name, tests, iterations`
**Variables Used:** `tokens_per_sec_list, total_cost, test_results, results, successes, tests, total_tokens, latencies`
**Implementation:**
```python
async def benchmark_model(self, model_name: str, tests: List[BenchmarkTest]=None, iterations: int=1) -> Dict[str, Any]:
    """
        Benchmark a single model.

        Args:
            model_name: Name of the model to test
            tests: List of tests to run (defaults to BENCHMARK_TESTS)
            iterations: Number of times to run each test

        Returns:
            Dictionary with benchmark results
        """
    tests = tests or BENCHMARK_TESTS
    logger.info(f'Starting benchmark for {model_name} with {len(tests)} tests')
    results = {'model': model_name, 'timestamp': datetime.utcnow().isoformat(), 'iterations': iterations, 'tests': [], 'summary': {'total_tests': len(tests), 'avg_latency_ms': 0, 'min_latency_ms': 0, 'max_latency_ms': 0, 'total_tokens': 0, 'avg_tokens_per_sec': 0, 'total_cost': 0.0, 'success_rate': 0.0}}
    latencies = []
    tokens_per_sec_list = []
    total_tokens = 0
    total_cost = 0.0
    successes = 0
    for test in tests:
        test_results = await self._run_test(model_name, test, iterations)
        results['tests'].append(test_results)
        if test_results['success']:
            successes += 1
        latencies.extend(test_results['latencies'])
        if test_results.get('tokens_per_sec'):
            tokens_per_sec_list.append(test_results['tokens_per_sec'])
        total_tokens += test_results.get('total_tokens', 0)
        total_cost += test_results.get('total_cost', 0.0)
    if latencies:
        results['summary']['avg_latency_ms'] = sum(latencies) / len(latencies)
        results['summary']['min_latency_ms'] = min(latencies)
        results['summary']['max_latency_ms'] = max(latencies)
    if tokens_per_sec_list:
        results['summary']['avg_tokens_per_sec'] = sum(tokens_per_sec_list) / len(tokens_per_sec_list)
    results['summary']['total_tokens'] = total_tokens
    results['summary']['total_cost'] = total_cost
    results['summary']['success_rate'] = successes / len(tests) * 100 if tests else 0
    self._save_results(model_name, results)
    return results
```

### Method: `_run_test`
**Logic & Purpose:**
```text
Run a single test multiple times
```

**Parameters:** `self, model_name, test, iterations`
**Variables Used:** `tps, result, test_results, quality, output, keywords_found`
**Implementation:**
```python
async def _run_test(self, model_name: str, test: BenchmarkTest, iterations: int) -> Dict[str, Any]:
    """Run a single test multiple times"""
    test_results = {'name': test.name, 'category': test.category, 'iterations': iterations, 'latencies': [], 'success': False, 'quality_score': 0.0, 'total_tokens': 0, 'total_cost': 0.0, 'tokens_per_sec': 0.0, 'errors': []}
    for i in range(iterations):
        try:
            result = await self._call_model(model_name, test.prompt)
            test_results['latencies'].append(result['duration_ms'])
            test_results['total_tokens'] += result.get('tokens', 0)
            test_results['total_cost'] += result.get('cost', 0.0)
            output = result.get('output', '').lower()
            keywords_found = sum((1 for kw in test.expected_keywords if kw.lower() in output))
            quality = keywords_found / len(test.expected_keywords) * 100 if test.expected_keywords else 100
            test_results['quality_score'] = max(test_results['quality_score'], quality)
            test_results['success'] = True
            if result['duration_ms'] > 0:
                tps = result.get('tokens', 0) / (result['duration_ms'] / 1000)
                test_results['tokens_per_sec'] = max(test_results['tokens_per_sec'], tps)
        except Exception as e:
            logger.error(f'Test {test.name} iteration {i + 1} failed: {e}')
            test_results['errors'].append(str(e))
    return test_results
```

### Method: `_call_model`
**Logic & Purpose:**
```text
Call the model via proxy API
```

**Parameters:** `self, model_name, prompt`
**Variables Used:** `data, start_time, duration_ms, output, usage, content, response, tokens`
**Implementation:**
```python
async def _call_model(self, model_name: str, prompt: str) -> Dict[str, Any]:
    """Call the model via proxy API"""
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.post(f'{self.base_url}/v1/messages', headers={'x-api-key': self.api_key, 'Content-Type': 'application/json'}, json={'model': model_name, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 500}, timeout=60.0)
        duration_ms = (time.time() - start_time) * 1000
        if response.status_code != 200:
            raise Exception(f'API returned {response.status_code}: {response.text}')
        data = response.json()
        content = data.get('content', [])
        output = content[0].get('text', '') if content else ''
        usage = data.get('usage', {})
        tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
        return {'duration_ms': duration_ms, 'output': output, 'tokens': tokens, 'cost': 0.0}
```

### Method: `_save_results`
**Logic & Purpose:**
```text
Save benchmark results to file
```

**Parameters:** `self, model_name, results`
**Variables Used:** `filename, filepath, timestamp, safe_model_name`
**Implementation:**
```python
def _save_results(self, model_name: str, results: Dict[str, Any]):
    """Save benchmark results to file"""
    safe_model_name = model_name.replace('/', '_').replace(':', '_')
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'benchmark_{safe_model_name}_{timestamp}.json'
    filepath = self.results_dir / filename
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f'Saved benchmark results to {filepath}')
```

### Method: `compare_models`
**Logic & Purpose:**
```text
Compare multiple models on the same test suite.

Returns comparative analysis.
```

**Parameters:** `self, model_names, tests`
**Variables Used:** `result, results, timestamp, comparison, tests, filepath`
**Implementation:**
```python
async def compare_models(self, model_names: List[str], tests: List[BenchmarkTest]=None) -> Dict[str, Any]:
    """
        Compare multiple models on the same test suite.

        Returns comparative analysis.
        """
    tests = tests or BENCHMARK_TESTS
    logger.info(f'Comparing {len(model_names)} models')
    results = []
    for model in model_names:
        result = await self.benchmark_model(model, tests)
        results.append(result)
    comparison = {'timestamp': datetime.utcnow().isoformat(), 'models': model_names, 'results': results, 'winner': {'fastest': min(results, key=lambda x: x['summary']['avg_latency_ms'])['model'], 'cheapest': min(results, key=lambda x: x['summary']['total_cost'])['model'], 'most_reliable': max(results, key=lambda x: x['summary']['success_rate'])['model']}}
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filepath = self.results_dir / f'comparison_{timestamp}.json'
    with open(filepath, 'w') as f:
        json.dump(comparison, f, indent=2)
    return comparison
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/usage/cost_calculator.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/usage/cost_calculator.py`

**Module Overview**: 
```text
Cost calculation utility for API requests.

Provides accurate cost estimates based on model pricing and token usage.
Pricing data updated as of November 2025.
```

## Global Presets & Variables
- `MODEL_PRICING` = `{'gpt-5': (0.015, 0.06), 'gpt-4o': (0.005, 0.015), 'gpt-4o-mini': (0.00015, 0.0006), 'gpt-4-turbo': (0.01, 0.03), 'gpt-4': (0.03, 0.06), 'gpt-3.5-turbo': (0.0015, 0.002), 'o1-preview': (0.015, 0.06), 'o1-mini': (0.003, 0.012), 'o3-mini': (0.003, 0.012), 'claude-3.5-sonnet': (0.003, 0.015), 'claude-3-sonnet': (0.003, 0.015), 'claude-3-haiku': (0.00025, 0.00125), 'claude-3-opus': (0.015, 0.075), 'claude-4-sonnet': (0.003, 0.015), 'claude-4': (0.015, 0.075), 'gemini-pro': (0.001, 0.002), 'gemini-1.5-pro': (0.001, 0.002), 'gemini-1.5-flash': (0.0001, 0.0003), 'gemini-2.0-flash': (0.0001, 0.0003), 'gemini-flash': (0.0001, 0.0003), 'llama-3.1-405b': (0.0027, 0.0027), 'llama-3.1-70b': (0.00088, 0.00088), 'llama-3.1-8b': (0.00018, 0.00018), 'llama-3.3-70b': (0.00088, 0.00088), 'llama-2-70b': (0.0007, 0.0009), 'mistral-large': (0.002, 0.006), 'mistral-medium': (0.00027, 0.00081), 'mistral-small': (6.8e-05, 0.000204), 'mixtral-8x7b': (0.00024, 0.00024), 'mixtral-8x22b': (0.00065, 0.00065), 'command-r-plus': (0.003, 0.015), 'command-r': (0.00015, 0.0006), 'command': (0.001, 0.002), 'qwen-2.5-72b': (0.00035, 0.0014), 'qwen-2.5-32b': (0.00018, 0.00072), 'qwen-2.5-14b': (0.0001, 0.0004), 'qwen-2.5-7b': (5e-05, 0.0002), 'qwen3-235b': (0.001, 0.004), 'deepseek-v3': (0.00027, 0.0011), 'deepseek-r1': (0.00055, 0.0022), 'deepseek-coder': (0.00014, 0.00028), 'grok-2': (0.002, 0.01), 'grok-beta': (0.005, 0.015), 'ollama': (0.0, 0.0), 'lmstudio': (0.0, 0.0)}`
- `OPENROUTER_MARKUP` = `1.05`
- `__all__` = `['calculate_cost', 'estimate_cost_from_text', 'get_model_pricing', 'format_cost', 'get_cost_summary']`

## Dependencies & Imports
typing.Dict, typing.Any, typing.Optional, typing.Tuple

## Feature Function: `get_model_pricing`
**Logic & Purpose:**
```text
Get pricing for a model.

Args:
    model_id: Model identifier (e.g., "gpt-4o", "claude-3-sonnet")

Returns:
    Tuple of (input_price_per_1m, output_price_per_1m) or None
```

**Parameters:** `model_id`
**Variables Used:** `model_lower`
**Implementation:**
```python
def get_model_pricing(model_id: str) -> Optional[Tuple[float, float]]:
    """
    Get pricing for a model.

    Args:
        model_id: Model identifier (e.g., "gpt-4o", "claude-3-sonnet")

    Returns:
        Tuple of (input_price_per_1m, output_price_per_1m) or None
    """
    model_lower = model_id.lower()
    if any((provider in model_lower for provider in ['ollama/', 'lmstudio/', 'local/'])):
        return (0.0, 0.0)
    if model_lower in MODEL_PRICING:
        return MODEL_PRICING[model_lower]
    for key, pricing in MODEL_PRICING.items():
        if key in model_lower:
            if 'openrouter' in model_lower:
                return (pricing[0] * OPENROUTER_MARKUP, pricing[1] * OPENROUTER_MARKUP)
            return pricing
    return None
```

---

## Feature Function: `calculate_cost`
**Logic & Purpose:**
```text
Calculate estimated cost for an API request.

Args:
    usage: Usage dict with token counts
           Expected keys: input_tokens, output_tokens, thinking_tokens
           Also supports: prompt_tokens, completion_tokens, reasoning_tokens
    model_id: Model identifier
    include_thinking_tokens: Whether to include thinking/reasoning tokens in cost

Returns:
    Estimated cost in USD
```

**Parameters:** `usage, model_id, include_thinking_tokens`
**Variables Used:** `output_tokens, details, total_cost, input_tokens, total_output, pricing, output_cost, thinking_tokens, input_cost`
**Implementation:**
```python
def calculate_cost(usage: Dict[str, Any], model_id: str, include_thinking_tokens: bool=True) -> float:
    """
    Calculate estimated cost for an API request.

    Args:
        usage: Usage dict with token counts
               Expected keys: input_tokens, output_tokens, thinking_tokens
               Also supports: prompt_tokens, completion_tokens, reasoning_tokens
        model_id: Model identifier
        include_thinking_tokens: Whether to include thinking/reasoning tokens in cost

    Returns:
        Estimated cost in USD
    """
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
    thinking_tokens = 0
    if include_thinking_tokens:
        thinking_tokens = usage.get('thinking_tokens', 0) or usage.get('reasoning_tokens', 0)
        details = usage.get('completion_tokens_details', {})
        if isinstance(details, dict):
            thinking_tokens = max(thinking_tokens, details.get('reasoning_tokens', 0))
    pricing = get_model_pricing(model_id)
    if not pricing:
        return 0.0
    input_price, output_price = pricing
    input_cost = input_tokens / 1000000 * input_price
    total_output = output_tokens + thinking_tokens
    output_cost = total_output / 1000000 * output_price
    total_cost = input_cost + output_cost
    return round(total_cost, 6)
```

---

## Feature Function: `estimate_cost_from_text`
**Logic & Purpose:**
```text
Estimate cost from raw text (without token counts).

Uses rough approximation: ~4 characters per token

Args:
    text: Input or output text
    model_id: Model identifier
    is_input: True if this is input text, False if output

Returns:
    Estimated cost in USD
```

**Parameters:** `text, model_id, is_input`
**Variables Used:** `pricing, price, estimated_tokens, cost`
**Implementation:**
```python
def estimate_cost_from_text(text: str, model_id: str, is_input: bool=True) -> float:
    """
    Estimate cost from raw text (without token counts).

    Uses rough approximation: ~4 characters per token

    Args:
        text: Input or output text
        model_id: Model identifier
        is_input: True if this is input text, False if output

    Returns:
        Estimated cost in USD
    """
    estimated_tokens = max(1, len(text) // 4)
    pricing = get_model_pricing(model_id)
    if not pricing:
        return 0.0
    input_price, output_price = pricing
    price = input_price if is_input else output_price
    cost = estimated_tokens / 1000000 * price
    return round(cost, 6)
```

---

## Feature Function: `format_cost`
**Logic & Purpose:**
```text
Format cost for display.

Args:
    cost: Cost in USD

Returns:
    Formatted string (e.g., "$0.0123", "$1.23", "<$0.0001")
```

**Parameters:** `cost`
**Implementation:**
```python
def format_cost(cost: float) -> str:
    """
    Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string (e.g., "$0.0123", "$1.23", "<$0.0001")
    """
    if cost == 0.0:
        return '$0.00'
    elif cost < 0.0001:
        return '<$0.0001'
    elif cost < 0.01:
        return f'${cost:.4f}'
    elif cost < 1.0:
        return f'${cost:.3f}'
    else:
        return f'${cost:.2f}'
```

---

## Feature Function: `get_cost_summary`
**Logic & Purpose:**
```text
Calculate cost summary for multiple requests.

Args:
    requests: List of request dicts with 'usage' and 'model' keys
    group_by: Grouping criterion - "model", "date", or "total"

Returns:
    Summary dict with cost breakdowns
```

**Parameters:** `requests, group_by`
**Variables Used:** `by_model, total_cost, model, cost`
**Implementation:**
```python
def get_cost_summary(requests: list[Dict[str, Any]], group_by: str='model') -> Dict[str, Any]:
    """
    Calculate cost summary for multiple requests.

    Args:
        requests: List of request dicts with 'usage' and 'model' keys
        group_by: Grouping criterion - "model", "date", or "total"

    Returns:
        Summary dict with cost breakdowns
    """
    if group_by == 'total':
        total_cost = sum((calculate_cost(req.get('usage', {}), req.get('model', '')) for req in requests))
        return {'total_cost': total_cost, 'total_requests': len(requests)}
    elif group_by == 'model':
        from collections import defaultdict
        by_model = defaultdict(lambda: {'cost': 0.0, 'requests': 0})
        for req in requests:
            model = req.get('model', 'unknown')
            cost = calculate_cost(req.get('usage', {}), model)
            by_model[model]['cost'] += cost
            by_model[model]['requests'] += 1
        return dict(by_model)
    else:
        raise ValueError(f'Unknown group_by: {group_by}')
```

---


