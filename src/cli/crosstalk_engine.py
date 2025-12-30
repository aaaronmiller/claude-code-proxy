#!/usr/bin/env python3
"""
Crosstalk Engine - Async Multi-Model Conversation Executor

Executes crosstalk sessions by routing messages between models in sequence,
applying jinja templates, and managing conversation history.

Paradigms:
- relay: Each model gets only the previous model's response
- memory: Each model gets full conversation history
- report: Models summarize before passing to next
- debate: Models can challenge and critique each other
"""

import asyncio
import json
import os
import time
import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict, field
from jinja2 import Template

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "templates"
SESSIONS_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "sessions"
CHECKPOINTS_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "checkpoints"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    model_id: str
    slot_id: int
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ConversationTranscript:
    """Full conversation record."""
    messages: List[Message]
    config: Dict[str, Any]
    started_at: str
    ended_at: str = ""
    
    def save(self, filename: Optional[str] = None) -> Path:
        """Save transcript to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = SESSIONS_DIR / f"session_{timestamp}.json"
        else:
            filename = Path(filename)
        
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        data = {
            "messages": [asdict(m) for m in self.messages],
            "config": self.config,
            "started_at": self.started_at,
            "ended_at": self.ended_at or datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def save_markdown(self, filename: Optional[str] = None) -> Path:
        """Save transcript to Markdown file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = SESSIONS_DIR / f"session_{timestamp}.md"
        else:
            filename = Path(filename)
        
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Build markdown content
        md = "# Crosstalk Session\n\n"
        md += f"**Started:** {self.started_at}\n"
        md += f"**Ended:** {self.ended_at}\n"
        md += f"**Paradigm:** {self.config.get('paradigm', 'relay')}\n"
        md += f"**Topology:** {self.config.get('topology', {}).get('type', 'ring')}\n"
        
        # Models summary
        models = self.config.get('models', [])
        if models:
            md += f"**Models:** {', '.join(m.get('model_id', 'unknown') for m in models)}\n"
        
        md += "\n---\n\n"
        
        # Messages
        for msg in self.messages:
            if msg.slot_id == 0:
                md += f"## 💬 User\n\n{msg.content}\n\n---\n\n"
            else:
                model_name = msg.model_id.split('/')[-1] if '/' in msg.model_id else msg.model_id
                md += f"## 🤖 AI {msg.slot_id} ({model_name})\n\n{msg.content}\n\n---\n\n"
        
        with open(filename, 'w') as f:
            f.write(md)
        
        return filename


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_template(template_name: str) -> Template:
    """Load a jinja template by name."""
    # Try file first
    template_path = TEMPLATES_DIR / f"{template_name}.j2"
    if template_path.exists():
        return Template(template_path.read_text())
    
    # Fallback to built-in templates
    from src.cli.crosstalk_studio import DEFAULT_TEMPLATES
    if template_name in DEFAULT_TEMPLATES:
        return Template(DEFAULT_TEMPLATES[template_name])
    
    # Ultimate fallback
    return Template("{{ message }}")


def apply_template(template_name: str, message: str, context: Dict[str, Any] = None) -> str:
    """Apply a jinja template to a message."""
    template = load_template(template_name)
    ctx = {"message": message}
    if context:
        ctx.update(context)
    return template.render(**ctx)


# ═══════════════════════════════════════════════════════════════════════════════
# API CALLING
# ═══════════════════════════════════════════════════════════════════════════════

async def call_model(
    model_id: str,
    messages: List[Dict[str, str]],
    system_prompt: str = "",
    temperature: float = 0.9,
    max_tokens: int = 4096,
    stream: bool = True,
    endpoint: str = "",  # NEW: Custom endpoint for this model
    api_key_env: str = ""  # NEW: Environment variable for API key
) -> AsyncGenerator[str, None]:
    """
    Call a model via OpenRouter API with streaming.
    
    Yields chunks of the response.
    
    Args:
        endpoint: Custom API endpoint (defaults to OpenRouter)
        api_key_env: Environment variable name for API key
    """
    # Use custom API key if specified, otherwise fallback chain
    if api_key_env:
        api_key = os.environ.get(api_key_env)
    else:
        api_key = (
            os.environ.get("OPENROUTER_API_KEY") or
            os.environ.get("OPENAI_API_KEY") or
            os.environ.get("PROVIDER_API_KEY")
        )
    
    if not api_key:
        yield "[ERROR: No API key configured]"
        return
    
    # Build messages array
    api_messages = []
    if system_prompt:
        api_messages.append({"role": "system", "content": system_prompt})
    api_messages.extend(messages)
    
    # Use custom endpoint if provided, otherwise default to OpenRouter
    api_endpoint = endpoint or "https://openrouter.ai/api/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                api_endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/crosstalk-studio",
                    "X-Title": "Crosstalk Studio"
                },
                json={
                    "model": model_id,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream
                }
            )
            
            if response.status_code != 200:
                yield f"[ERROR: HTTP {response.status_code}]"
                return
            
            if stream:
                # Stream response
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
            else:
                # Non-streaming
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                yield content
                
        except Exception as e:
            yield f"[ERROR: {str(e)}]"


# ═══════════════════════════════════════════════════════════════════════════════
# PARADIGM IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def build_messages_relay(
    conversation: List[Message],
    current_slot: int
) -> List[Dict[str, str]]:
    """
    Relay paradigm: Model only sees the previous message.
    """
    # Find the last message (not from this slot)
    for msg in reversed(conversation):
        if msg.slot_id != current_slot:
            return [{"role": "user", "content": msg.content}]
    
    return []


def build_messages_memory(
    conversation: List[Message],
    current_slot: int
) -> List[Dict[str, str]]:
    """
    Memory paradigm: Model sees full conversation history.
    """
    messages = []
    for msg in conversation:
        role = "assistant" if msg.slot_id == current_slot else "user"
        messages.append({"role": role, "content": msg.content})
    return messages


def build_messages_debate(
    conversation: List[Message],
    current_slot: int
) -> List[Dict[str, str]]:
    """
    Debate paradigm: Model sees history and is encouraged to critique.
    """
    messages = build_messages_memory(conversation, current_slot)
    
    if messages:
        # Add debate instruction
        messages.append({
            "role": "user",
            "content": "[DEBATE MODE: Challenge, critique, or extend the previous arguments. Be rigorous.]"
        })
    
    return messages


# ═══════════════════════════════════════════════════════════════════════════════
# TOPOLOGY ORDER GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def get_model_order_ring(models, topology) -> List:
    """Ring topology: Sequential or custom order."""
    if topology.order:
        # Custom order - map slot IDs to model objects
        order_map = {m.slot_id: m for m in models}
        return [order_map.get(slot_id, models[0]) for slot_id in topology.order if slot_id in order_map]
    return models


def get_model_order_star(models, topology) -> List:
    """Star topology: Center speaks to each spoke, spokes respond to center."""
    center_id = topology.center
    center = next((m for m in models if m.slot_id == center_id), models[0])
    spokes = [m for m in models if m.slot_id != center_id]
    
    # Interleave: center, spoke1, center, spoke2, ...
    result = []
    for spoke in spokes:
        result.append(center)
        result.append(spoke)
    return result


def get_model_order_mesh(models, topology) -> List:
    """Mesh topology: Every model talks to every other model."""
    result = []
    for speaker in models:
        for listener in models:
            if speaker.slot_id != listener.slot_id:
                result.append(speaker)
    return result


def get_model_order_chain(models, topology) -> List:
    """Chain topology: Linear progression, same as ring but conceptually different."""
    return models


def get_model_order_random(models, topology) -> List:
    """Random topology: Shuffle models each round."""
    import random
    shuffled = models.copy()
    random.shuffle(shuffled)
    return shuffled


def get_model_order_custom(models, topology) -> List:
    """Custom topology: Use exact pattern specified."""
    pattern = topology.pattern if hasattr(topology, 'pattern') and topology.pattern else []
    if not pattern:
        return models
    # Pattern is list of (speaker_idx, listener_idx) tuples - return speakers for this round
    # For simplicity, return models in order of their appearance in pattern
    seen = []
    for speaker, _ in pattern:
        if speaker not in seen:
            for m in models:
                if m.slot_id == speaker:
                    seen.append(m)
                    break
    return seen if seen else models


def get_model_order_tournament(models, topology) -> List:
    """Tournament topology: Bracket-style elimination."""
    # For now, return pairs for each match
    return models[:2] if len(models) >= 2 else models


# ═══════════════════════════════════════════════════════════════════════════════
# META-PROMPTS & SUMMARIZATION
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_summary(
    conversation: List[Message],
    summarizer_model: str = "anthropic/claude-3-haiku",
    summary_prompt: str = "Summarize the key points of this discussion so far in 2-3 sentences."
) -> str:
    """Generate a summary of the conversation so far."""
    # Build conversation text
    conv_text = "\n\n".join([
        f"[{m.model_id}]: {m.content[:500]}..." if len(m.content) > 500 else f"[{m.model_id}]: {m.content}"
        for m in conversation[-20:]  # Last 20 messages max
    ])
    
    messages = [{"role": "user", "content": f"{summary_prompt}\n\nConversation:\n{conv_text}"}]
    
    summary = ""
    async for chunk in call_model(
        model_id=summarizer_model,
        messages=messages,
        system_prompt="You are a concise summarizer. Provide brief, accurate summaries.",
        temperature=0.3,
        max_tokens=500,
        stream=True
    ):
        summary += chunk
    
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKPOINTING
# ═══════════════════════════════════════════════════════════════════════════════

def save_checkpoint(
    transcript: 'ConversationTranscript',
    session_id: str,
    turn: int
) -> Path:
    """Save a checkpoint of the current conversation state."""
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    
    checkpoint_file = CHECKPOINTS_DIR / f"{session_id}_turn_{turn}.json"
    
    data = {
        "messages": [asdict(m) for m in transcript.messages],
        "config": transcript.config,
        "started_at": transcript.started_at,
        "checkpoint_turn": turn,
        "checkpoint_time": datetime.now().isoformat()
    }
    
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    console.print(f"[dim]💾 Checkpoint saved: turn {turn}[/]")
    return checkpoint_file


def load_checkpoint(checkpoint_file: Path) -> Dict[str, Any]:
    """Load a checkpoint file."""
    with open(checkpoint_file, 'r') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT MODIFIERS (APPEND/PREPEND)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_context_modifiers(
    message: str,
    model_slot,
    is_input: bool = True
) -> str:
    """
    Apply append/prepend context modifiers to a message.
    
    Args:
        message: The original message
        model_slot: The model slot with optional append/prepend fields
        is_input: True if this is input to the model (append), False if output (prepend)
    """
    # Get append (added to messages this model receives)
    append = getattr(model_slot, 'append', None) or ''
    # Get prepend (added before messages this model sends)
    prepend = getattr(model_slot, 'prepend', None) or ''
    
    if is_input and append:
        message = f"{message}\n\n{append}"
    elif not is_input and prepend:
        message = f"{prepend}{message}"
    
    return message


# ═══════════════════════════════════════════════════════════════════════════════
# NOVELTY/REPETITION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple Jaccard similarity between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def detect_repetition(conversation: List[Message], threshold: float = 0.85) -> bool:
    """
    Detect if the conversation has become repetitive.
    
    Returns True if recent messages are too similar.
    """
    if len(conversation) < 4:
        return False
    
    # Check last 4 messages for similarity
    recent = [m.content for m in conversation[-4:] if m.role == "assistant"]
    
    if len(recent) < 2:
        return False
    
    for i in range(len(recent) - 1):
        similarity = calculate_similarity(recent[i], recent[i + 1])
        if similarity > threshold:
            return True
    
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# VOTING & CONSENSUS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Vote:
    """A single vote from a model."""
    model_id: str
    slot_id: int
    choice: str
    confidence: float = 1.0
    reasoning: str = ""


def tally_votes(
    votes: List[Vote],
    method: str = "majority",
    weights: Dict[int, float] = None
) -> Dict[str, Any]:
    """
    Tally votes and determine consensus.
    
    Methods:
        - majority: Simple majority wins
        - weighted: Weighted by model confidence or custom weights
        - unanimous: All must agree
    
    Returns dict with:
        - winner: The winning choice
        - counts: Vote counts per choice
        - consensus: Whether consensus was reached
    """
    if not votes:
        return {"winner": None, "counts": {}, "consensus": False}
    
    weights = weights or {}
    counts: Dict[str, float] = {}
    
    for vote in votes:
        weight = weights.get(vote.slot_id, 1.0) * vote.confidence
        counts[vote.choice] = counts.get(vote.choice, 0) + weight
    
    sorted_choices = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_choices[0][0] if sorted_choices else None
    
    # Check consensus based on method
    if method == "unanimous":
        consensus = len(set(v.choice for v in votes)) == 1
    elif method == "majority":
        total = sum(counts.values())
        consensus = counts.get(winner, 0) > total / 2
    else:  # weighted
        consensus = True  # Winner by weight
    
    return {
        "winner": winner,
        "counts": dict(counts),
        "consensus": consensus,
        "method": method
    }


async def request_vote(
    model_slot,
    question: str,
    options: List[str],
    conversation: List[Message]
) -> Vote:
    """Request a vote from a model on a question."""
    options_str = ", ".join(options)
    vote_prompt = f"""
Based on the discussion so far, please vote on this question:

{question}

Options: {options_str}

Respond with ONLY your choice from the options, followed by a brief reason.
Format: CHOICE: [your choice]
REASON: [brief explanation]
"""
    
    messages = [{"role": "user", "content": vote_prompt}]
    
    response = ""
    async for chunk in call_model(
        model_id=model_slot.model_id,
        messages=messages,
        system_prompt="You are participating in a vote. Be decisive.",
        temperature=0.3,
        max_tokens=200
    ):
        response += chunk
    
    # Parse response
    choice = options[0]  # Default
    reasoning = ""
    
    for line in response.split("\n"):
        if line.upper().startswith("CHOICE:"):
            choice_text = line.split(":", 1)[1].strip()
            for opt in options:
                if opt.lower() in choice_text.lower():
                    choice = opt
                    break
        elif line.upper().startswith("REASON:"):
            reasoning = line.split(":", 1)[1].strip()
    
    return Vote(
        model_id=model_slot.model_id,
        slot_id=model_slot.slot_id,
        choice=choice,
        confidence=1.0,
        reasoning=reasoning
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RoutingRule:
    """A rule for conditional message routing."""
    condition_type: str  # "keyword", "length", "confidence"
    condition_value: Any
    route_to: int  # Slot ID to route to
    comment: str = ""


def evaluate_routing_rules(
    message: str,
    rules: List[RoutingRule],
    default_route: int = None
) -> Optional[int]:
    """
    Evaluate routing rules against a message.
    
    Returns the slot ID to route to, or None if no rule matches.
    """
    for rule in rules:
        if rule.condition_type == "keyword":
            # Check if any keyword is in message
            keywords = rule.condition_value if isinstance(rule.condition_value, list) else [rule.condition_value]
            for kw in keywords:
                if kw.lower() in message.lower():
                    return rule.route_to
        
        elif rule.condition_type == "length":
            # Check message length threshold
            if len(message) > rule.condition_value:
                return rule.route_to
        
        elif rule.condition_type == "question":
            # Check if message is a question
            if "?" in message:
                return rule.route_to
    
    return default_route


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-STAGE SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConversationStage:
    """A stage in a multi-stage conversation."""
    name: str
    rounds: int
    topology: str = "ring"
    append_all: str = ""  # Appended to all messages in this stage
    transition_prompt: str = ""  # Prompt when transitioning to next stage


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

async def run_crosstalk(session) -> Optional[ConversationTranscript]:
    """
    Execute a crosstalk session.
    
    Args:
        session: CrosstalkSession object with models, rounds, etc.
    
    Returns:
        ConversationTranscript with full conversation record
    """
    from src.cli.crosstalk_studio import ModelSlot, CrosstalkSession, TopologyConfig, StopConditions
    
    # Get topology info
    topology = getattr(session, 'topology', None)
    topo_type = topology.type if topology else "ring"
    infinite = getattr(session, 'infinite', False)
    stop_conditions = getattr(session, 'stop_conditions', None)
    summarize_every = getattr(session, 'summarize_every', 0)
    
    mode_str = "∞ infinite" if infinite else f"{session.rounds} rounds"
    
    console.print(Panel(
        "[bold cyan]🔮 CROSSTALK SESSION STARTING[/]\n\n"
        f"[dim]Models: {len(session.models)} | Mode: {mode_str} | "
        f"Paradigm: {session.paradigm} | Topology: {topo_type}[/]",
        border_style="cyan"
    ))
    
    # Initialize conversation
    conversation: List[Message] = []
    transcript = ConversationTranscript(
        messages=[],
        config={
            "models": [asdict(m) for m in session.models],
            "rounds": session.rounds,
            "paradigm": session.paradigm,
            "topology": asdict(topology) if topology else {"type": "ring"},
            "infinite": infinite,
            "initial_prompt": session.initial_prompt
        },
        started_at=datetime.now().isoformat()
    )
    
    # Add initial prompt as first message
    initial_msg = Message(
        role="user",
        content=session.initial_prompt,
        model_id="user",
        slot_id=0
    )
    conversation.append(initial_msg)
    transcript.messages.append(initial_msg)
    
    console.print(f"\n[bold magenta]USER:[/] {session.initial_prompt}\n")
    
    # Build message function based on paradigm
    paradigm_builders = {
        "relay": build_messages_relay,
        "memory": build_messages_memory,
        "debate": build_messages_debate,
        "report": build_messages_relay,  # Similar to relay
    }
    build_messages = paradigm_builders.get(session.paradigm, build_messages_relay)
    
    # Topology order generators
    topo_generators = {
        "ring": get_model_order_ring,
        "star": get_model_order_star,
        "mesh": get_model_order_mesh,
        "chain": get_model_order_chain,
        "random": get_model_order_random,
        "custom": get_model_order_custom,
        "tournament": get_model_order_tournament,
    }
    get_order = topo_generators.get(topo_type, get_model_order_ring)
    
    # Run conversation rounds
    try:
        round_num = 0
        max_rounds = 10000 if infinite else session.rounds
        start_time = time.time()
        total_cost = 0.0
        should_stop = False
        stop_reason = ""
        
        while round_num < max_rounds and not should_stop:
            round_num += 1
            
            # Check time limit before round
            if stop_conditions and stop_conditions.max_time_seconds > 0:
                elapsed = time.time() - start_time
                if elapsed >= stop_conditions.max_time_seconds:
                    stop_reason = f"⏱️  Time limit ({stop_conditions.max_time_seconds}s)"
                    should_stop = True
                    break
            
            # Check cost limit before round
            if stop_conditions and stop_conditions.max_cost_dollars > 0:
                if total_cost >= stop_conditions.max_cost_dollars:
                    stop_reason = f"💰 Cost limit (${stop_conditions.max_cost_dollars:.2f})"
                    should_stop = True
                    break
            
            if infinite:
                elapsed_str = f"{time.time() - start_time:.0f}s"
                console.print(f"\n[bold white]━━━ ROUND {round_num} (∞) [{elapsed_str}] ━━━[/]\n")
            else:
                console.print(f"\n[bold white]━━━ ROUND {round_num}/{session.rounds} ━━━[/]\n")
            
            # Get model order for this round based on topology
            model_order = get_order(session.models, topology)
            
            for model_slot in model_order:
                slot_id = model_slot.slot_id
                model_id = model_slot.model_id
                
                console.print(f"[bold cyan]AI {slot_id} ({model_slot.display_name}):[/]")
                
                # Build messages for this model
                messages = build_messages(conversation, slot_id)
                
                # Apply jinja template to the last message
                if messages:
                    last_content = messages[-1]["content"]
                    templated = apply_template(
                        model_slot.jinja_template,
                        last_content,
                        {
                            "round": round_num,
                            "slot": slot_id,
                            "model": model_id
                        }
                    )
                    messages[-1]["content"] = templated
                
                # Call the model with streaming
                full_response = ""
                async for chunk in call_model(
                    model_id=model_id,
                    messages=messages,
                    system_prompt=model_slot.system_prompt,
                    temperature=model_slot.temperature,
                    max_tokens=model_slot.max_tokens,
                    stream=True,
                    endpoint=getattr(model_slot, 'endpoint', '') or '',
                    api_key_env=getattr(model_slot, 'api_key_env', '') or ''
                ):
                    full_response += chunk
                    console.print(chunk, end="")
                
                console.print("\n")
                
                # Estimate cost (rough: ~$0.0001 per 100 chars for gpt-4o-mini)
                total_cost += len(full_response) * 0.000001
                
                # Check for stop keywords
                if stop_conditions and stop_conditions.stop_keywords:
                    for kw in stop_conditions.stop_keywords:
                        if kw.lower() in full_response.lower():
                            stop_reason = f"🔑 Stop keyword: '{kw}'"
                            should_stop = True
                            break
                
                # Record message
                msg = Message(
                    role="assistant",
                    content=full_response,
                    model_id=model_id,
                    slot_id=slot_id
                )
                conversation.append(msg)
                transcript.messages.append(msg)
            
            # === META-PROMPTS: Generate summary every N rounds ===
            if summarize_every > 0 and round_num % summarize_every == 0:
                console.print(f"\n[bold yellow]📝 Generating summary...[/]")
                summarizer_model = session.models[0].model_id if session.models else "anthropic/claude-3-haiku"
                summary = await generate_summary(
                    conversation,
                    summarizer_model=summarizer_model,
                    summary_prompt="Summarize the key points and progress made so far."
                )
                
                # Inject summary as system context
                summary_msg = Message(
                    role="system",
                    content=f"[SUMMARY after round {round_num}]: {summary}",
                    model_id="summarizer",
                    slot_id=0
                )
                conversation.append(summary_msg)
                transcript.messages.append(summary_msg)
                console.print(f"[dim]Summary: {summary[:200]}...[/]\n")
            
            # === CHECKPOINTING: Save every 10 rounds for long sessions ===
            checkpoint_every = getattr(session, 'checkpoint_every', 10) if infinite else 0
            if checkpoint_every > 0 and round_num % checkpoint_every == 0:
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_checkpoint(transcript, session_id, round_num)
            
            # === REPETITION DETECTION: Stop if too repetitive ===
            if infinite and detect_repetition(conversation):
                stop_reason = "🔄 Conversation became repetitive"
                should_stop = True
        
        # === FINAL ROUND VOTING ===
        final_vote = getattr(session, 'final_round_vote', None)
        if final_vote and not should_stop:
            console.print(Panel(
                "[bold yellow]🗳️ FINAL ROUND VOTING[/]",
                border_style="yellow"
            ))
            
            question = final_vote.get('question', 'What is your final verdict?')
            options = final_vote.get('options', ['yes', 'no', 'undecided'])
            method = final_vote.get('tally_method', 'majority')
            weights = final_vote.get('weights', {})
            
            votes = []
            for model_slot in session.models:
                console.print(f"[dim]Requesting vote from {model_slot.display_name}...[/]")
                vote = await request_vote(model_slot, question, options, conversation)
                votes.append(vote)
                console.print(f"  [cyan]{model_slot.display_name}[/]: {vote.choice} - {vote.reasoning[:50]}...")
            
            result = tally_votes(votes, method=method, weights=weights)
            
            console.print(Panel(
                f"[bold]Vote Results:[/]\n\n"
                f"Winner: [bold cyan]{result['winner']}[/]\n"
                f"Counts: {result['counts']}\n"
                f"Consensus: {'✓ Yes' if result['consensus'] else '✗ No'}",
                border_style="green" if result['consensus'] else "yellow"
            ))
            
            # Add vote result to transcript
            vote_msg = Message(
                role="system",
                content=f"[VOTE RESULT]: Winner={result['winner']}, Counts={result['counts']}, Consensus={result['consensus']}",
                model_id="voting_system",
                slot_id=0
            )
            transcript.messages.append(vote_msg)
        
        # Session complete
        transcript.ended_at = datetime.now().isoformat()
        elapsed = time.time() - start_time
        
        if should_stop and stop_reason:
            console.print(Panel(
                f"[bold yellow]⚡ SESSION STOPPED[/]\n\n"
                f"[dim]Reason: {stop_reason}[/]\n"
                f"[dim]Rounds: {round_num} | Messages: {len(transcript.messages)} | "
                f"Time: {elapsed:.1f}s | Est. cost: ${total_cost:.4f}[/]",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                "[bold green]✓ CROSSTALK SESSION COMPLETE[/]\n\n"
                f"[dim]Messages: {len(transcript.messages)} | Time: {elapsed:.1f}s | "
                f"Est. cost: ${total_cost:.4f}[/]",
                border_style="green"
            ))
        
        # Offer to save
        from rich.prompt import Confirm
        if Confirm.ask("\nSave transcript?"):
            filename = transcript.save()
            console.print(f"[green]Saved: {filename}[/]")
        
        input("\nPress Enter to continue...")
        return transcript
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted by user[/]")
        transcript.ended_at = datetime.now().isoformat()
        
        from rich.prompt import Confirm
        if Confirm.ask("Save partial transcript?"):
            filename = transcript.save()
            console.print(f"[green]Saved: {filename}[/]")
        
        input("\nPress Enter to continue...")
        return transcript
    
    except Exception as e:
        console.print(f"\n[red]Error during session: {e}[/]")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to continue...")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

async def quick_crosstalk(
    prompt: str,
    model1: str = "anthropic/claude-3-opus",
    model2: str = "anthropic/claude-3-opus",
    rounds: int = 3,
    paradigm: str = "relay"
):
    """Quick crosstalk session from command line."""
    from src.cli.crosstalk_studio import CrosstalkSession, ModelSlot
    
    session = CrosstalkSession(
        models=[
            ModelSlot(slot_id=1, model_id=model1),
            ModelSlot(slot_id=2, model_id=model2),
        ],
        rounds=rounds,
        paradigm=paradigm,
        initial_prompt=prompt
    )
    
    await run_crosstalk(session)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crosstalk Engine CLI")
    parser.add_argument("--prompt", "-p", type=str, required=True,
                       help="Initial prompt to start the conversation")
    parser.add_argument("--model1", "-m1", type=str, default="anthropic/claude-3-opus",
                       help="First model ID")
    parser.add_argument("--model2", "-m2", type=str, default="anthropic/claude-3-opus",
                       help="Second model ID")
    parser.add_argument("--rounds", "-r", type=int, default=3,
                       help="Number of conversation rounds")
    parser.add_argument("--paradigm", type=str, default="relay",
                       choices=["relay", "memory", "debate", "report"],
                       help="Conversation paradigm")
    
    args = parser.parse_args()
    
    asyncio.run(quick_crosstalk(
        prompt=args.prompt,
        model1=args.model1,
        model2=args.model2,
        rounds=args.rounds,
        paradigm=args.paradigm
    ))
