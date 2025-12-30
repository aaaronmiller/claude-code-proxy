"""
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
"""

import asyncio
import json
import logging
import os
import httpx
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Database paths
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
RANKINGS_PATH = MODELS_DIR / "model_rankings.json"

# Default free models for ranking (fallback if API fails)
DEFAULT_FREE_MODELS = [
    "kwaicoder/kwaicoder-ds-v1",
    "deepseek/deepseek-chat-v3-0324:free",
    "qwen/qwen3-235b-a22b:free",
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
]

# Tool definitions for the LLM
SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information about LLM models, benchmarks, and coding performance. Use this to find recent benchmark scores, community feedback, and model comparisons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Be specific, e.g., 'DeepSeek V3 HumanEval benchmark score 2024' or 'best free LLM for Python coding'"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-5)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }
]


@dataclass
class ModelRanking:
    """Ranking for a model based on coding capability."""
    model_id: str
    rank: int
    coding_score: float  # 0-100
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    best_for: List[str] = field(default_factory=list)
    context_length: int = 0
    is_free: bool = True
    reasoning: str = ""
    sources: List[str] = field(default_factory=list)  # Web sources used
    ranked_at: str = ""


def get_ranker_model() -> str:
    """Get the model to use for ranking."""
    return os.environ.get(
        "RANKER_MODEL",
        os.environ.get("SCRAPER_MODEL", "kwaicoder/kwaicoder-ds-v1")
    )


def get_ranker_api_key() -> Optional[str]:
    """Get API key for ranker."""
    return (
        os.environ.get("RANKER_API_KEY") or
        os.environ.get("SCRAPER_API_KEY") or
        os.environ.get("OPENROUTER_API_KEY") or
        os.environ.get("OPENAI_API_KEY") or
        os.environ.get("PROVIDER_API_KEY")
    )


def get_exa_api_key() -> Optional[str]:
    """Get Exa API key for web search."""
    return os.environ.get("EXA_API_KEY")


def should_use_web_search() -> bool:
    """Check if web search should be used for ranking."""
    if os.environ.get("RANKER_USE_SEARCH", "true").lower() != "true":
        return False
    # Only enable if we have Exa key
    return get_exa_api_key() is not None


async def exa_search(query: str, num_results: int = 3) -> List[Dict]:
    """
    Search using Exa API for current model information.
    
    Returns list of search results with title, url, and snippet.
    """
    api_key = get_exa_api_key()
    if not api_key:
        return []
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "query": query,
                    "numResults": min(num_results, 5),
                    "useAutoprompt": True,
                    "type": "neural",
                    "contents": {
                        "text": {"maxCharacters": 500}
                    }
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Exa search failed: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("text", "")[:300]
                })
            return results
            
        except Exception as e:
            logger.error(f"Exa search error: {e}")
            return []


async def execute_tool_call(tool_name: str, arguments: Dict) -> str:
    """Execute a tool call and return the result."""
    if tool_name == "web_search":
        query = arguments.get("query", "")
        num_results = arguments.get("num_results", 3)
        
        results = await exa_search(query, num_results)
        
        if not results:
            return "No search results found. Please proceed with your existing knowledge."
        
        formatted = []
        for r in results:
            formatted.append(f"**{r['title']}**\n{r['url']}\n{r['snippet']}\n")
        
        return "\n---\n".join(formatted)
    
    return f"Unknown tool: {tool_name}"


async def fetch_free_models_from_openrouter() -> List[Dict]:
    """Fetch list of free models from OpenRouter API."""
    api_key = get_ranker_api_key()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch models: HTTP {response.status_code}")
                return []
            
            data = response.json()
            models = data.get("data", [])
            
            # Filter to free models only
            free_models = []
            for model in models:
                pricing = model.get("pricing", {})
                prompt_price = float(pricing.get("prompt", 0))
                completion_price = float(pricing.get("completion", 0))
                
                if prompt_price == 0 and completion_price == 0:
                    free_models.append({
                        "id": model.get("id"),
                        "name": model.get("name"),
                        "context_length": model.get("context_length", 0),
                        "created": model.get("created", 0),
                        "description": model.get("description", "")[:200],
                    })
            
            return free_models
            
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []


async def rank_models_with_llm(
    models: List[Dict],
    use_web_search: bool = True
) -> List[ModelRanking]:
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
        logger.warning("No API key available for ranking")
        return []
    
    # Prepare model list for prompt
    model_summary = "\n".join([
        f"- {m['id']}: {m.get('name', 'Unknown')} (ctx: {m.get('context_length', 0):,})"
        for m in models[:30]
    ])
    
    # Enhanced system prompt with tool usage instructions
    system_prompt = """You are an expert at evaluating LLM models for coding tasks.

## YOUR MISSION
Rank the provided free models by their **coding capability** using factual data.

## TOOLS AVAILABLE
You have access to a `web_search` tool. USE IT to find:
1. Recent benchmark scores (HumanEval, MBPP, SWE-Bench, etc.)
2. Community comparisons and reviews
3. Official model release announcements with capabilities

## EVALUATION CRITERIA (in order of importance)
1. **Coding benchmarks**: HumanEval pass@1, MBPP, SWE-Bench scores
2. **Architecture quality**: Parameter count, training data, specialization
3. **Context length**: Larger = better for codebases
4. **Community feedback**: Real-world coding performance
5. **Recency**: Newer models often perform better

## EVALUATION FOCUS
Models should be good at:
- Code generation (Python, JavaScript, TypeScript priority)
- Code completion and refactoring
- Debugging and error analysis
- Understanding large codebases

## PROCESS
1. First, search for benchmark data on the most promising models
2. Cross-reference with community feedback
3. Produce your final rankings

## OUTPUT FORMAT
After gathering data, return ONLY a JSON array:
```json
[
  {
    "model_id": "provider/model-name",
    "rank": 1,
    "coding_score": 85,
    "strengths": ["high HumanEval score", "good at Python"],
    "weaknesses": ["slower inference"],
    "best_for": ["python", "debugging", "refactoring"],
    "reasoning": "Brief explanation with data sources"
  }
]
```

Rank the top 10-15 models. Only include models from the provided list."""

    user_prompt = f"""Please rank these FREE models for coding tasks:

{model_summary}

IMPORTANT: Use the web_search tool to find current benchmark data before ranking.
Search for terms like:
- "[model name] HumanEval benchmark"
- "[model name] coding performance"
- "best free LLM for coding 2024"

After researching, return your rankings as a JSON array."""

    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Tool loop - allow multiple tool calls
    max_tool_iterations = 5
    search_count = 0
    sources_used = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for iteration in range(max_tool_iterations):
            try:
                request_body = {
                    "model": ranker_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4000,
                }
                
                # Add tools if search is enabled and we haven't exhausted searches
                if use_web_search and should_use_web_search() and search_count < 3:
                    request_body["tools"] = SEARCH_TOOLS
                    request_body["tool_choice"] = "auto"
                
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_body
                )
                
                if response.status_code != 200:
                    logger.error(f"Ranking API error: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                
                # Check for tool calls
                tool_calls = message.get("tool_calls", [])
                
                if tool_calls:
                    # Add assistant message with tool calls
                    messages.append(message)
                    
                    # Execute each tool call
                    for tool_call in tool_calls:
                        func = tool_call.get("function", {})
                        tool_name = func.get("name")
                        
                        try:
                            arguments = json.loads(func.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            arguments = {}
                        
                        print(f"   🔍 Searching: {arguments.get('query', '')[:50]}...")
                        
                        result = await execute_tool_call(tool_name, arguments)
                        search_count += 1
                        
                        # Track sources
                        if "http" in result:
                            for line in result.split("\n"):
                                if line.startswith("http"):
                                    sources_used.append(line.strip())
                        
                        # Add tool result
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "content": result
                        })
                    
                    # Continue loop to get next response
                    continue
                
                # No tool calls - this should be the final response
                content = message.get("content", "")
                
                # Parse JSON from response
                json_start = content.find("[")
                json_end = content.rfind("]") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    rankings_data = json.loads(json_str)
                    
                    rankings = []
                    for item in rankings_data:
                        ranking = ModelRanking(
                            model_id=item.get("model_id", ""),
                            rank=item.get("rank", 99),
                            coding_score=item.get("coding_score", 0),
                            strengths=item.get("strengths", []),
                            weaknesses=item.get("weaknesses", []),
                            best_for=item.get("best_for", []),
                            reasoning=item.get("reasoning", ""),
                            sources=sources_used[:5],  # Top 5 sources
                            ranked_at=datetime.now().isoformat()
                        )
                        rankings.append(ranking)
                    
                    return sorted(rankings, key=lambda r: r.rank)
                else:
                    logger.error("Could not parse JSON from LLM response")
                    logger.debug(f"Response content: {content[:500]}")
                    break
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                break
            except Exception as e:
                logger.error(f"Ranking error: {e}")
                break
    
    return []


def save_rankings(rankings: List[ModelRanking]):
    """Save rankings to local database."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "updated_at": datetime.now().isoformat(),
        "ranker_model": get_ranker_model(),
        "web_search_used": should_use_web_search(),
        "rankings": [asdict(r) for r in rankings]
    }
    
    with open(RANKINGS_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(rankings)} rankings to {RANKINGS_PATH}")


def load_rankings() -> List[ModelRanking]:
    """Load rankings from local database."""
    if not RANKINGS_PATH.exists():
        return []
    
    try:
        with open(RANKINGS_PATH, 'r') as f:
            data = json.load(f)
        
        rankings = []
        for item in data.get("rankings", []):
            # Handle missing 'sources' field from old data
            if 'sources' not in item:
                item['sources'] = []
            rankings.append(ModelRanking(**item))
        
        return sorted(rankings, key=lambda r: r.rank)
    except Exception as e:
        logger.error(f"Error loading rankings: {e}")
        return []


def get_top_coding_models(n: int = 5) -> List[ModelRanking]:
    """Get top N coding models from saved rankings."""
    rankings = load_rankings()
    return rankings[:n]


async def update_rankings():
    """Fetch free models and update rankings."""
    print("🔄 Fetching free models from OpenRouter...")
    free_models = await fetch_free_models_from_openrouter()
    
    if not free_models:
        print("❌ No free models found. Using defaults...")
        free_models = [{"id": m, "name": m.split("/")[-1]} for m in DEFAULT_FREE_MODELS]
    
    print(f"📊 Found {len(free_models)} free models")
    print(f"🤖 Ranking with: {get_ranker_model()}")
    
    if should_use_web_search():
        print("🌐 Web search ENABLED (Exa API)")
    else:
        exa_key = get_exa_api_key()
        if not exa_key:
            print("⚠️  Web search disabled (set EXA_API_KEY to enable)")
        else:
            print("⚠️  Web search disabled (set RANKER_USE_SEARCH=true to enable)")
    
    print("\n🔍 Analyzing models...")
    rankings = await rank_models_with_llm(free_models)
    
    if rankings:
        save_rankings(rankings)
        print(f"\n✅ Ranked {len(rankings)} models for coding\n")
        print("Top models for coding:")
        for r in rankings[:10]:
            strengths = ", ".join(r.strengths[:2]) if r.strengths else "—"
            print(f"  {r.rank:2}. {r.model_id:<45} Score: {r.coding_score:<3} | {strengths}")
        
        if rankings[0].sources:
            print(f"\n📚 Sources used: {len(rankings[0].sources)}")
    else:
        print("❌ Failed to generate rankings")


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Powered Model Ranker with Web Search")
    parser.add_argument("--rank-free", action="store_true",
                       help="Rank free models for coding (uses web search if available)")
    parser.add_argument("--top", type=int, default=5,
                       help="Show top N coding models")
    parser.add_argument("--show", action="store_true",
                       help="Show current rankings")
    
    args = parser.parse_args()
    
    if args.show:
        rankings = load_rankings()
        if rankings:
            print(f"\n🏆 Model Rankings for Coding (from {RANKINGS_PATH.name})\n")
            for r in rankings:
                strengths = ", ".join(r.strengths[:2]) if r.strengths else "—"
                print(f"  {r.rank:2}. {r.model_id:<45} Score: {r.coding_score}")
                print(f"      Strengths: {strengths}")
                print(f"      Best for: {', '.join(r.best_for[:3]) if r.best_for else '—'}")
                if r.sources:
                    print(f"      Sources: {len(r.sources)} web results")
                print()
        else:
            print("No rankings found. Run --rank-free first.")
    elif args.rank_free:
        asyncio.run(update_rankings())
    else:
        # Show top N
        rankings = load_rankings()
        if rankings:
            print(f"\n🏆 Top {args.top} Models for Coding:\n")
            for r in rankings[:args.top]:
                print(f"  {r.rank}. {r.model_id} (score: {r.coding_score})")
        else:
            print("No rankings found. Run --rank-free to generate rankings.")
