#!/usr/bin/env python3
"""
Dreams of an Electric Mind Importer

Imports configuration from Andy Ayrey's Infinite Backrooms format.
Parses URLs from dreams-of-an-electric-mind.webflow.io and extracts:
- actors (persona names)
- models (model IDs)
- temp (temperatures)
- system prompts per actor
- context arrays

Also exports sessions in compatible format.

Reference: https://dreams-of-an-electric-mind.webflow.io/
"""

import re
import json
import httpx
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path


@dataclass
class BackroomsActor:
    """Actor configuration from Infinite Backrooms format."""
    name: str
    model_id: str
    temperature: float
    system_prompt: str
    context: List[Dict[str, str]]


@dataclass
class BackroomsConfig:
    """Full configuration parsed from Infinite Backrooms."""
    actors: List[BackroomsActor]
    scenario_name: str
    source_url: str


def parse_backrooms_config(text: str, source_url: str = "") -> Optional[BackroomsConfig]:
    """
    Parse Infinite Backrooms configuration from raw text.
    
    Format example:
    ```
    actors: backrooms-8b-schizo-magic, claude-4-freeform
    models: openpipe:backrooms-fullset-8b, claude-sonnet-4-20250514
    temp: 0.96, 1
    
    <backrooms-8b-schizo-magic-openpipe:backrooms-fullset-8b#SYSTEM>
    System prompt here
    
    <claude-4-freeform-claude-sonnet-4-20250514#SYSTEM>
    Another system prompt
    ```
    """
    actors = []
    
    # Extract actors line
    actors_match = re.search(r'actors:\s*([^\n]+)', text)
    if not actors_match:
        return None
    actor_names = [a.strip() for a in actors_match.group(1).split(',')]
    
    # Extract models line
    models_match = re.search(r'models:\s*([^\n]+)', text)
    if not models_match:
        return None
    model_ids = [m.strip() for m in models_match.group(1).split(',')]
    
    # Extract temps line
    temps_match = re.search(r'temp:\s*([^\n]+)', text)
    temps = [0.9] * len(actor_names)  # Default
    if temps_match:
        try:
            temps = [float(t.strip()) for t in temps_match.group(1).split(',')]
        except ValueError:
            pass
    
    # Ensure lists are same length
    while len(model_ids) < len(actor_names):
        model_ids.append(model_ids[-1] if model_ids else "anthropic/claude-3-opus")
    while len(temps) < len(actor_names):
        temps.append(temps[-1] if temps else 0.9)
    
    # Extract system prompts per actor
    for i, actor_name in enumerate(actor_names):
        model_id = model_ids[i]
        temp = temps[i]
        
        # Build pattern for this actor's system prompt
        # Format: <actor_name-model_id#SYSTEM> ... </tag> or until next tag
        system_prompt = ""
        context = []
        
        # Try to find system prompt
        pattern = rf'<{re.escape(actor_name)}-[^#]+#SYSTEM>\s*(.*?)(?=<[^>]+#|$)'
        sys_match = re.search(pattern, text, re.DOTALL)
        if sys_match:
            system_prompt = sys_match.group(1).strip()
            # Clean up escaped newlines
            system_prompt = system_prompt.replace('\\n', '\n').replace('\\\\n', '\n')
        
        # Try to find context
        ctx_pattern = rf'<{re.escape(actor_name)}-[^#]+#CONTEXT>\s*(\[.*?\])'
        ctx_match = re.search(ctx_pattern, text, re.DOTALL)
        if ctx_match:
            try:
                context = json.loads(ctx_match.group(1).replace('\\n', '\n'))
            except json.JSONDecodeError:
                pass
        
        # Normalize model ID (openpipe: prefix, etc.)
        if not '/' in model_id and ':' in model_id:
            # OpenPipe format: openpipe:name -> name
            model_id = model_id.split(':')[-1]
        elif not '/' in model_id:
            # Bare model name - assume Anthropic
            if 'claude' in model_id.lower():
                model_id = f"anthropic/{model_id}"
            elif 'gpt' in model_id.lower():
                model_id = f"openai/{model_id}"
            elif 'gemini' in model_id.lower():
                model_id = f"google/{model_id}"
        
        actors.append(BackroomsActor(
            name=actor_name,
            model_id=model_id,
            temperature=temp,
            system_prompt=system_prompt,
            context=context
        ))
    
    # Extract scenario name from URL or text
    scenario_name = "imported"
    if source_url:
        # Try to extract from URL
        name_match = re.search(r'scenario[_-]([^.]+)', source_url)
        if name_match:
            scenario_name = name_match.group(1)
    
    return BackroomsConfig(
        actors=actors,
        scenario_name=scenario_name,
        source_url=source_url
    )


async def fetch_backrooms_url(url: str) -> Optional[BackroomsConfig]:
    """
    Fetch and parse configuration from a Dreams of Electric Mind URL.
    
    Args:
        url: URL to a conversation page on dreams-of-an-electric-mind.webflow.io
        
    Returns:
        BackroomsConfig if parsing succeeds, None otherwise
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            
            text = response.text
            
            # Find the code block with configuration
            code_match = re.search(r'<code[^>]*>(.*?)</code>', text, re.DOTALL)
            if code_match:
                config_text = code_match.group(1)
                # Unescape HTML entities
                config_text = config_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                return parse_backrooms_config(config_text, url)
            
            # Try to find preformatted text
            pre_match = re.search(r'```(.*?)```', text, re.DOTALL)
            if pre_match:
                return parse_backrooms_config(pre_match.group(1), url)
            
            return None
            
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return None


def export_backrooms_format(
    actors: List[Dict],
    conversation: List[Dict],
    scenario_name: str = "crosstalk"
) -> str:
    """
    Export session in Infinite Backrooms compatible format.
    
    Args:
        actors: List of actor configurations
        conversation: List of conversation messages
        scenario_name: Name for this scenario
        
    Returns:
        Text in Infinite Backrooms format
    """
    lines = []
    
    # Header
    actor_names = [a.get('name', f"ai_{i+1}") for i, a in enumerate(actors)]
    model_ids = [a.get('model_id', 'unknown') for a in actors]
    temps = [str(a.get('temperature', 0.9)) for a in actors]
    
    lines.append(f"actors: {', '.join(actor_names)}")
    lines.append(f"models: {', '.join(model_ids)}")
    lines.append(f"temp: {', '.join(temps)}")
    lines.append("")
    
    # System prompts
    for actor in actors:
        name = actor.get('name', 'unknown')
        model = actor.get('model_id', 'unknown')
        system = actor.get('system_prompt', '')
        
        lines.append(f"<{name}-{model}#SYSTEM>")
        lines.append(system)
        lines.append("")
    
    # Conversation
    lines.append("---CONVERSATION---")
    lines.append("")
    
    for msg in conversation:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        model = msg.get('model_id', 'unknown')
        
        lines.append(f"<{role}|{model}>")
        lines.append(content)
        lines.append("")
    
    return '\n'.join(lines)


def convert_to_crosstalk_session(config: BackroomsConfig):
    """
    Convert BackroomsConfig to CrosstalkSession format.
    
    Returns a dict that can be used to create a CrosstalkSession.
    """
    from src.cli.crosstalk_studio import ModelSlot
    
    models = []
    for i, actor in enumerate(config.actors):
        slot = ModelSlot(
            slot_id=i + 1,
            model_id=actor.model_id,
            system_prompt_inline=actor.system_prompt,
            jinja_template="basic",
            temperature=actor.temperature,
        )
        models.append(slot)
    
    # Extract initial prompt from first actor's context if available
    initial_prompt = ""
    for actor in config.actors:
        if actor.context:
            for ctx in actor.context:
                if ctx.get('role') == 'user':
                    initial_prompt = ctx.get('content', '')
                    break
            if initial_prompt:
                break
    
    return {
        "models": models,
        "initial_prompt": initial_prompt,
        "paradigm": "relay",
        "rounds": 10,
        "source_url": config.source_url,
        "scenario_name": config.scenario_name
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test the importer."""
    import asyncio
    
    test_url = "https://dreams-of-an-electric-mind.webflow.io/dreams/conversation-1748868371-scenario-backrooms-x-sonnet4-txt"
    
    print(f"Fetching: {test_url}")
    config = await fetch_backrooms_url(test_url)
    
    if config:
        print(f"\nScenario: {config.scenario_name}")
        print(f"Actors: {len(config.actors)}")
        
        for actor in config.actors:
            print(f"\n  {actor.name}:")
            print(f"    Model: {actor.model_id}")
            print(f"    Temp: {actor.temperature}")
            print(f"    System: {actor.system_prompt[:100]}...")
    else:
        print("Failed to parse configuration")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
