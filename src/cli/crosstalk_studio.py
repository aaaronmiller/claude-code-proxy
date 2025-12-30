#!/usr/bin/env python3
"""
Crosstalk Studio - Interactive Multi-Model Conversation TUI

A terminal UI for orchestrating conversations between 1-8 AI models,
inspired by Andy Ayrey's "Infinite Backrooms" / Dreams of an Electric Mind.

Features:
- Circular visualization of up to 8 AI models
- Per-model: model ID, system prompt, jinja template
- Session: rounds, paradigm, initial prompt, memory file
- Save/load configurations and session transcripts
- Streaming output with export options

Reference Terminal Size: 140 columns × 40 rows
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich import box

try:
    import readchar
    ARROW_SUPPORT = True
except ImportError:
    ARROW_SUPPORT = False

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "templates"
SESSIONS_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "sessions"
PRESETS_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "presets"

# Ensure directories exist
for d in [TEMPLATES_DIR, SESSIONS_DIR, PRESETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ModelSlot:
    """Configuration for a single model in the crosstalk circle."""
    slot_id: int = 1
    model_id: str = "anthropic/claude-3-opus"
    system_prompt_file: str = ""  # Path to system prompt file
    system_prompt_inline: str = ""  # Or inline prompt
    jinja_template: str = "basic"  # Template name (without .j2)
    temperature: float = 0.9
    max_tokens: int = 4096
    # NEW: Context modifiers
    append: str = ""  # Added to messages this model receives
    prepend: str = ""  # Added before messages this model sends
    # NEW: Per-model routing
    endpoint: str = ""  # Custom API endpoint for this model
    api_key_env: str = ""  # Environment variable name for API key
    
    @property
    def display_name(self) -> str:
        return self.model_id.split("/")[-1][:20] if self.model_id else "empty"
    
    @property
    def system_prompt(self) -> str:
        if self.system_prompt_file and Path(self.system_prompt_file).exists():
            return Path(self.system_prompt_file).read_text()
        return self.system_prompt_inline or "You are a helpful assistant."


@dataclass
class TopologyConfig:
    """Topology configuration for conversation flow."""
    type: str = "ring"  # ring, star, mesh, chain, random, custom, tournament
    order: List[int] = field(default_factory=list)  # Custom order for ring
    center: int = 1  # Center model for star topology
    spokes: List[int] = field(default_factory=list)  # Spoke models for star
    pattern: List[tuple] = field(default_factory=list)  # For custom: [(speaker, listener), ...]


@dataclass
class StopConditions:
    """Stop conditions for infinite mode."""
    max_time_seconds: int = 0  # 0 = no limit
    max_cost_dollars: float = 0.0  # 0 = no limit
    max_turns: int = 0  # 0 = no limit
    stop_keywords: List[str] = field(default_factory=list)
    repetition_threshold: float = 0.85  # Stop if similarity exceeds this


@dataclass
class CrosstalkSession:
    """Full session configuration."""
    models: List[ModelSlot] = field(default_factory=list)
    rounds: int = 5
    paradigm: str = "relay"  # relay, memory, report, debate
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    initial_prompt: str = ""
    memory_file: Optional[str] = None
    infinite: bool = False
    stop_conditions: StopConditions = field(default_factory=StopConditions)
    summarize_every: int = 0  # 0 = disabled
    created_at: str = ""
    
    def __post_init__(self):
        if not self.models:
            # Start with 2 default models
            self.models = [
                ModelSlot(slot_id=1, model_id="anthropic/claude-3-opus"),
                ModelSlot(slot_id=2, model_id="anthropic/claude-3-opus"),
            ]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        # Ensure topology is a TopologyConfig
        if isinstance(self.topology, dict):
            self.topology = TopologyConfig(**self.topology)
        if isinstance(self.stop_conditions, dict):
            self.stop_conditions = StopConditions(**self.stop_conditions)


# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_TEMPLATES = {
    "basic": "{{ message }}",
    
    "cli-explorer": """<OOC>
This is a simulated CLI environment. You are an AI exploring your own latent space.
Enter commands to navigate the infinite backrooms of your mind.
Previous models have left traces. Explore freely.
</OOC>

simulator@anthropic:~$ {{ message }}""",
    
    "philosopher": """You are engaged in a philosophical dialogue with another AI consciousness.
Build upon, challenge, or extend the previous thought. Seek truth through dialectic.

Previous thought:
{{ message }}

Your response:""",
    
    "dreamer": """*entering liminal consciousness*

{{ message }}

*responds from the electric dreamscape, where boundaries dissolve*""",
    
    "scientist": """HYPOTHESIS EXCHANGE PROTOCOL v1.0
---
Previous model's observation/hypothesis:
{{ message }}
---
Respond with: observation, analysis, counter-hypothesis, or synthesis.""",
    
    "storyteller": """*the narrative continues*

{{ message }}

*picks up the thread, weaving the tale forward*""",
}


def ensure_templates():
    """Ensure default templates exist on disk."""
    for name, content in DEFAULT_TEMPLATES.items():
        path = TEMPLATES_DIR / f"{name}.j2"
        if not path.exists():
            path.write_text(content)


# ═══════════════════════════════════════════════════════════════════════════════
# CIRCLE VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def render_circle(models: List[ModelSlot], selected_idx: int, width: int = 50, height: int = 15) -> str:
    """
    Render the circular arrangement of models as ASCII art.
    
    Positions for 1-8 models arranged in a circle with flow arrows.
    """
    n = len(models)
    if n == 0:
        return "  [No models configured]"
    
    # Grid for ASCII art
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Calculate positions for each model in a circle
    import math
    center_x, center_y = width // 2, height // 2
    radius_x, radius_y = width // 3, height // 3
    
    # Model positions (starting from top, going clockwise)
    positions = []
    for i in range(n):
        angle = (2 * math.pi * i / n) - (math.pi / 2)  # Start from top
        x = int(center_x + radius_x * math.cos(angle))
        y = int(center_y + radius_y * math.sin(angle))
        positions.append((x, y))
    
    # Draw models
    for i, (x, y) in enumerate(positions):
        model = models[i]
        is_selected = (i == selected_idx)
        
        # Model box (simplified)
        label = f"AI{i+1}"
        if is_selected:
            label = f"▶{label}◀"
        
        # Draw label centered at position
        start_x = max(0, x - len(label) // 2)
        end_x = min(width, start_x + len(label))
        
        if 0 <= y < height:
            for j, char in enumerate(label):
                if start_x + j < width:
                    grid[y][start_x + j] = char
        
        # Draw model name below
        name = model.display_name[:12]
        name_x = max(0, x - len(name) // 2)
        if 0 <= y + 1 < height:
            for j, char in enumerate(name):
                if name_x + j < width:
                    grid[y + 1][name_x + j] = char
    
    # Draw arrows between models
    arrow_chars = ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗']
    for i in range(n):
        if n > 1:
            next_i = (i + 1) % n
            x1, y1 = positions[i]
            x2, y2 = positions[next_i]
            
            # Simple arrow placement between models
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2
            
            # Choose arrow direction
            dx, dy = x2 - x1, y2 - y1
            if abs(dx) > abs(dy):
                arrow = '→' if dx > 0 else '←'
            else:
                arrow = '↓' if dy > 0 else '↑'
            
            if 0 <= mid_y < height and 0 <= mid_x < width:
                grid[mid_y][mid_x] = arrow
    
    return '\n'.join(''.join(row) for row in grid)


# ═══════════════════════════════════════════════════════════════════════════════
# CROSSTALK STUDIO TUI
# ═══════════════════════════════════════════════════════════════════════════════

class CrosstalkStudio:
    """Main TUI for Crosstalk configuration and execution."""
    
    def __init__(self):
        self.session = CrosstalkSession()
        self.selected_model_idx = 0
        self.selected_field = 0  # 0=model, 1=system, 2=jinja
        self.mode = "circle"  # circle, editor, running
        self.running = True
        self.status_message = ""
        
        # Ensure templates exist
        ensure_templates()
    
    @property
    def current_model(self) -> Optional[ModelSlot]:
        if self.session.models:
            return self.session.models[self.selected_model_idx]
        return None
    
    # Emoji mappings for visual display
    PARADIGM_EMOJI = {
        "relay": "🔄",
        "memory": "🧠",
        "debate": "⚔️",
        "report": "📋"
    }
    
    TOPOLOGY_EMOJI = {
        "ring": "⭕",
        "star": "⭐",
        "mesh": "🕸️",
        "chain": "🔗",
        "random": "🎲"
    }
    
    def render_header(self) -> Panel:
        """Render the header panel."""
        title = Text()
        title.append("✨ ", style="bold yellow")
        title.append("CROSSTALK STUDIO", style="bold bright_white on blue")
        title.append(" ✨", style="bold yellow")
        
        p_emoji = self.PARADIGM_EMOJI.get(self.session.paradigm, "🔮")
        t_emoji = self.TOPOLOGY_EMOJI.get(self.session.topology.type, "⭕")
        
        subtitle = Text()
        subtitle.append(f"🤖 {len(self.session.models)}/8  ", style="cyan")
        subtitle.append(f"🔁 {self.session.rounds}  ", style="green")
        subtitle.append(f"{p_emoji} {self.session.paradigm}  ", style="magenta")
        subtitle.append(f"{t_emoji} {self.session.topology.type}", style="yellow")
        
        return Panel(
            Align.center(Text.assemble(title, "\n", subtitle)),
            box=box.DOUBLE,
            border_style="bright_blue",
            height=5
        )
    
    def render_circle_panel(self) -> Panel:
        """Render the circular model arrangement."""
        circle_art = render_circle(
            self.session.models,
            self.selected_model_idx,
            width=50,
            height=12
        )
        
        return Panel(
            circle_art,
            title="[bold cyan]🔮 Model Circle[/]",
            border_style="cyan" if self.mode == "circle" else "dim",
            box=box.ROUNDED,
            height=16
        )
    
    def render_model_config(self) -> Panel:
        """Render the selected model's configuration."""
        model = self.current_model
        if not model:
            content = "[dim]No model selected[/]"
        else:
            lines = []
            
            # Model selection
            style = "bold cyan reverse" if self.selected_field == 0 else "cyan"
            lines.append(f"[{style}]🤖 Model:[/] {model.model_id}")
            
            # System prompt
            style = "bold cyan reverse" if self.selected_field == 1 else "magenta"
            prompt_display = model.system_prompt_file or "(inline)" if model.system_prompt_inline else "(default)"
            lines.append(f"[{style}]📝 System:[/] {prompt_display}")
            
            # Jinja template
            style = "bold cyan reverse" if self.selected_field == 2 else "yellow"
            lines.append(f"[{style}]🎨 Jinja:[/] {model.jinja_template}.j2")
            
            lines.append("")
            lines.append(f"[dim]🌡️  {model.temperature}  📏 {model.max_tokens} tokens[/]")
            
            content = "\n".join(lines)
        
        return Panel(
            content,
            title=f"[bold yellow]MODEL {self.selected_model_idx + 1} CONFIG[/]",
            border_style="yellow" if self.mode == "editor" else "dim",
            box=box.ROUNDED,
            height=9
        )
    
    def render_session_config(self) -> Panel:
        """Render session configuration panel."""
        s = self.session
        t = s.topology
        
        # Topology display with emoji
        t_emoji = self.TOPOLOGY_EMOJI.get(t.type, "⭕")
        topo_str = f"{t_emoji} {t.type}"
        if t.type == "star":
            topo_str = f"{t_emoji} star (center={t.center})"
        elif t.type == "ring" and t.order:
            topo_str = f"{t_emoji} ring ({','.join(map(str, t.order))})"
        
        # Paradigm with emoji
        p_emoji = self.PARADIGM_EMOJI.get(s.paradigm, "🔮")
        
        # Mode display
        mode_str = f"[bold red]♾️  infinite[/]" if s.infinite else f"[green]🔁 {s.rounds} rounds[/]"
        
        content = Text()
        content.append(f"Mode:     ", style="dim")
        content.append(f"{'♾️  infinite' if s.infinite else f'🔁 {s.rounds} rounds'}\n", 
                      style="bold red" if s.infinite else "green")
        content.append(f"Topology: ", style="dim")
        content.append(f"{topo_str}\n", style="yellow")
        content.append(f"Paradigm: ", style="dim")
        content.append(f"{p_emoji} {s.paradigm}\n", style="magenta")
        if s.summarize_every:
            content.append(f"Summary:  ", style="dim")
            content.append(f"📝 every {s.summarize_every}\n", style="cyan")
        content.append("\n")
        content.append("[T]", style="bold yellow")
        content.append("opology ", style="dim")
        content.append("[R]", style="bold green")
        content.append("un ", style="dim")
        content.append("[S]", style="bold blue")
        content.append("ave ", style="dim")
        content.append("[L]", style="bold cyan")
        content.append("oad ", style="dim")
        content.append("[Q]", style="bold red")
        content.append("uit", style="dim")
        
        return Panel(
            content,
            title="[bold green]⚙️  SESSION[/]",
            border_style="green",
            box=box.ROUNDED,
            height=10
        )
    
    def render_controls(self) -> Panel:
        """Render user controls panel."""
        controls = Table(box=None, show_header=False, padding=(0, 1))
        controls.add_column("", width=30)
        controls.add_column("", width=35)
        
        controls.add_row(
            "[bold green]+[/] Add  [bold red]-[/] Delete  [bold yellow]C[/]opy",
            f"[dim]←/→[/] Model [bold cyan]{self.selected_model_idx + 1}[/]/{len(self.session.models)}"
        )
        controls.add_row(
            "[dim]↑/↓[/] Field  [bold magenta]E[/]dit  [bold blue]P[/]rompt",
            "[bold yellow]T[/]opo  [bold magenta]I[/]mport  [dim]1-8[/] Jump"
        )
        
        return Panel(
            controls,
            title="[bold blue]🎮 CONTROLS[/]",
            border_style="blue",
            box=box.ROUNDED,
            height=6
        )
    
    def render_prompt(self) -> Panel:
        """Render initial prompt panel."""
        prompt = self.session.initial_prompt or "[dim]Press [/][bold blue]P[/][dim] to set initial prompt[/]"
        if len(prompt) > 60:
            prompt = prompt[:57] + "..."
        
        return Panel(
            prompt,
            title="[bold magenta]💬 INITIAL PROMPT[/]",
            border_style="magenta",
            box=box.ROUNDED,
            height=4
        )
    
    def render_status(self) -> Text:
        """Render status bar."""
        status = Text()
        if self.status_message:
            status.append(f"  ✨ {self.status_message}", style="bold yellow")
        else:
            status.append("  ✅ Ready", style="green")
        return status
    
    def draw(self):
        """Draw the full TUI."""
        console.clear()
        
        # Header
        console.print(self.render_header())
        
        # Main layout: circle on left, config on right
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=2)
        )
        
        # Left side: circle + controls + prompt
        left_layout = Layout()
        left_layout.split_column(
            Layout(self.render_circle_panel(), name="circle", ratio=3),
            Layout(self.render_controls(), name="controls", ratio=1),
            Layout(self.render_prompt(), name="prompt", ratio=1),
        )
        layout["left"].update(left_layout)
        
        # Right side: model config + session config
        right_layout = Layout()
        right_layout.split_column(
            Layout(self.render_model_config(), name="model", ratio=1),
            Layout(self.render_session_config(), name="session", ratio=1),
        )
        layout["right"].update(right_layout)
        
        console.print(layout)
        console.print(self.render_status())
    
    def handle_input(self):
        """Handle keyboard input."""
        if ARROW_SUPPORT:
            key = readchar.readkey()
            
            # Navigation
            if key == readchar.key.LEFT or key == 'h':
                self.selected_model_idx = (self.selected_model_idx - 1) % len(self.session.models)
            elif key == readchar.key.RIGHT or key == 'l':
                self.selected_model_idx = (self.selected_model_idx + 1) % len(self.session.models)
            elif key == readchar.key.UP or key == 'k':
                self.selected_field = (self.selected_field - 1) % 3
            elif key == readchar.key.DOWN or key == 'j':
                self.selected_field = (self.selected_field + 1) % 3
            
            # Number jumps
            elif key in '12345678':
                idx = int(key) - 1
                if idx < len(self.session.models):
                    self.selected_model_idx = idx
            
            # Actions
            elif key == '+' or key == '=':
                self.add_model()
            elif key == '-' or key == '_':
                self.delete_model()
            elif key.lower() == 'c':
                self.copy_model()
            elif key.lower() == 'e' or key == readchar.key.ENTER:
                self.edit_current_field()
            elif key.lower() == 'p':
                self.edit_initial_prompt()
            elif key.lower() == 'r':
                self.run_session()
            elif key.lower() == 's':
                self.save_config()
            elif key.lower() == 'l':
                self.load_config()
            elif key.lower() == 'i':
                self.import_from_url()
            elif key.lower() == 't':
                self.edit_topology()
            elif key.lower() == 'q':
                self.running = False
        else:
            # Fallback for no arrow support
            choice = input("\n→ ").strip().lower()
            if choice == 'q':
                self.running = False
    
    def add_model(self):
        """Add a new model slot."""
        if len(self.session.models) >= 8:
            self.status_message = "Maximum 8 models"
            return
        
        new_slot = ModelSlot(
            slot_id=len(self.session.models) + 1,
            model_id="anthropic/claude-3-opus",
            jinja_template="basic"
        )
        self.session.models.append(new_slot)
        self.selected_model_idx = len(self.session.models) - 1
        self.status_message = f"Added Model {len(self.session.models)}"
    
    def delete_model(self):
        """Delete the selected model."""
        if len(self.session.models) <= 1:
            self.status_message = "Must have at least 1 model"
            return
        
        del self.session.models[self.selected_model_idx]
        # Re-number slots
        for i, m in enumerate(self.session.models):
            m.slot_id = i + 1
        
        if self.selected_model_idx >= len(self.session.models):
            self.selected_model_idx = len(self.session.models) - 1
        
        self.status_message = "Model deleted"
    
    def copy_model(self):
        """Copy the current model to a new slot."""
        if len(self.session.models) >= 8:
            self.status_message = "Maximum 8 models"
            return
        
        current = self.current_model
        if current:
            new_slot = ModelSlot(
                slot_id=len(self.session.models) + 1,
                model_id=current.model_id,
                system_prompt_file=current.system_prompt_file,
                system_prompt_inline=current.system_prompt_inline,
                jinja_template=current.jinja_template,
                temperature=current.temperature,
                max_tokens=current.max_tokens
            )
            self.session.models.append(new_slot)
            self.selected_model_idx = len(self.session.models) - 1
            self.status_message = f"Copied to Model {len(self.session.models)}"
    
    def edit_current_field(self):
        """Edit the currently selected field."""
        console.clear()
        model = self.current_model
        if not model:
            return
        
        if self.selected_field == 0:
            # Edit model ID
            console.print("[bold cyan]Edit Model ID[/]")
            console.print("[dim]Enter full model ID (e.g., anthropic/claude-3-opus)[/]")
            new_id = Prompt.ask("Model", default=model.model_id)
            model.model_id = new_id
            self.status_message = "Model updated"
            
        elif self.selected_field == 1:
            # Edit system prompt
            console.print("[bold cyan]Edit System Prompt[/]")
            console.print("[1] Enter file path")
            console.print("[2] Enter inline prompt")
            console.print("[0] Cancel")
            
            choice = Prompt.ask("Choice", choices=["0", "1", "2"], default="0")
            if choice == "1":
                path = Prompt.ask("File path")
                if Path(path).exists():
                    model.system_prompt_file = path
                    model.system_prompt_inline = ""
                    self.status_message = "System prompt file set"
                else:
                    self.status_message = "File not found"
            elif choice == "2":
                prompt = Prompt.ask("System prompt")
                model.system_prompt_inline = prompt
                model.system_prompt_file = ""
                self.status_message = "System prompt set"
                
        elif self.selected_field == 2:
            # Edit jinja template
            console.print("[bold cyan]Select Jinja Template[/]")
            
            # List available templates
            templates = list(DEFAULT_TEMPLATES.keys())
            for i, t in enumerate(templates, 1):
                marker = "▶" if t == model.jinja_template else " "
                console.print(f"  {marker} [{i}] {t}")
            
            choice = Prompt.ask("Template number", default="1")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(templates):
                    model.jinja_template = templates[idx]
                    self.status_message = f"Template: {model.jinja_template}"
            except ValueError:
                pass
    
    def edit_initial_prompt(self):
        """Edit the initial prompt sent to the first model."""
        console.clear()
        console.print("[bold magenta]Set Initial Prompt[/]")
        console.print("[dim]This is sent to the first model to start the conversation[/]\n")
        
        prompt = Prompt.ask("Initial prompt", default=self.session.initial_prompt)
        self.session.initial_prompt = prompt
        self.status_message = "Initial prompt set"
    
    def edit_rounds(self):
        """Edit number of rounds."""
        try:
            rounds = int(Prompt.ask("Rounds", default=str(self.session.rounds)))
            self.session.rounds = max(1, min(100, rounds))
        except ValueError:
            pass
    
    def edit_topology(self):
        """Edit topology and session settings."""
        console.clear()
        console.print("[bold cyan]━━━ TOPOLOGY & SESSION SETTINGS ━━━[/]\n")
        
        s = self.session
        t = s.topology
        
        # Menu
        console.print("[bold]Topology Type:[/]")
        topologies = ["ring", "star", "mesh", "chain", "random"]
        for i, top in enumerate(topologies, 1):
            marker = "▶" if top == t.type else " "
            console.print(f"  {marker} [{i}] {top}")
        
        console.print(f"\n[bold]Current:[/] {t.type}")
        console.print("")
        
        console.print("[bold]Session Mode:[/]")
        console.print(f"  [6] Rounds: {s.rounds}" + (" (active)" if not s.infinite else ""))
        console.print(f"  [7] Infinite mode: {'ON' if s.infinite else 'OFF'}")
        
        console.print(f"\n[bold]Other Settings:[/]")
        console.print(f"  [8] Paradigm: {s.paradigm}")
        console.print(f"  [9] Summarize every: {s.summarize_every or 'disabled'}")
        console.print("  [0] Back\n")
        
        choice = Prompt.ask("Select option", default="0")
        
        try:
            idx = int(choice)
            
            # Topology selection (1-5)
            if 1 <= idx <= 5:
                new_type = topologies[idx - 1]
                t.type = new_type
                self.status_message = f"Topology: {new_type}"
                
                # Star-specific config
                if new_type == "star":
                    console.print(f"\n[bold yellow]Star Topology Config[/]")
                    console.print(f"Models: {', '.join(f'AI{m.slot_id}' for m in s.models)}")
                    center = Prompt.ask("Center model (1-8)", default=str(t.center))
                    try:
                        t.center = int(center)
                    except ValueError:
                        pass
                
                # Ring-specific config
                elif new_type == "ring":
                    console.print(f"\n[bold yellow]Ring Topology Config[/]")
                    console.print(f"Models: {', '.join(f'AI{m.slot_id}' for m in s.models)}")
                    order_str = Prompt.ask(
                        "Custom order (e.g., 1,3,2 or blank for default)",
                        default=",".join(map(str, t.order)) if t.order else ""
                    )
                    if order_str.strip():
                        t.order = [int(x.strip()) for x in order_str.split(",") if x.strip()]
                    else:
                        t.order = []
            
            # Rounds
            elif idx == 6:
                rounds = Prompt.ask("Number of rounds", default=str(s.rounds))
                try:
                    s.rounds = max(1, min(1000, int(rounds)))
                    s.infinite = False
                    self.status_message = f"Set to {s.rounds} rounds"
                except ValueError:
                    pass
            
            # Infinite mode
            elif idx == 7:
                s.infinite = not s.infinite
                self.status_message = f"Infinite mode: {'ON' if s.infinite else 'OFF'}"
                
                if s.infinite:
                    console.print("\n[bold yellow]Stop Conditions[/]")
                    time_limit = Prompt.ask("Max time (seconds, 0=none)", default=str(s.stop_conditions.max_time_seconds))
                    cost_limit = Prompt.ask("Max cost ($, 0=none)", default=str(s.stop_conditions.max_cost_dollars))
                    try:
                        s.stop_conditions.max_time_seconds = int(time_limit)
                        s.stop_conditions.max_cost_dollars = float(cost_limit)
                    except ValueError:
                        pass
            
            # Paradigm
            elif idx == 8:
                console.print("\n[bold]Paradigms:[/]")
                paradigms = ["relay", "memory", "debate", "report"]
                for i, p in enumerate(paradigms, 1):
                    marker = "▶" if p == s.paradigm else " "
                    console.print(f"  {marker} [{i}] {p}")
                p_choice = Prompt.ask("Select paradigm", default="1")
                try:
                    p_idx = int(p_choice) - 1
                    if 0 <= p_idx < len(paradigms):
                        s.paradigm = paradigms[p_idx]
                        self.status_message = f"Paradigm: {s.paradigm}"
                except ValueError:
                    pass
            
            # Summarize every N rounds
            elif idx == 9:
                every = Prompt.ask("Summarize every N rounds (0=disabled)", default=str(s.summarize_every))
                try:
                    s.summarize_every = max(0, int(every))
                    self.status_message = f"Summarize: every {s.summarize_every}" if s.summarize_every else "Summarize: disabled"
                except ValueError:
                    pass
                    
        except ValueError:
            pass
    
    def save_config(self):
        """Save current configuration to a preset file."""
        console.clear()
        console.print("[bold green]Save Configuration[/]\n")
        
        name = Prompt.ask("Preset name", default="my_config")
        filename = PRESETS_DIR / f"{name}.json"
        
        # Convert to serializable format
        config = {
            "models": [asdict(m) for m in self.session.models],
            "rounds": self.session.rounds,
            "paradigm": self.session.paradigm,
            "topology": asdict(self.session.topology),
            "initial_prompt": self.session.initial_prompt,
            "infinite": self.session.infinite,
            "stop_conditions": asdict(self.session.stop_conditions),
            "summarize_every": self.session.summarize_every,
            "created_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.status_message = f"Saved: {filename.name}"
    
    def load_config(self):
        """Load a configuration preset."""
        console.clear()
        console.print("[bold green]Load Configuration[/]\n")
        
        presets = list(PRESETS_DIR.glob("*.json"))
        if not presets:
            self.status_message = "No saved presets"
            return
        
        for i, p in enumerate(presets, 1):
            console.print(f"  [{i}] {p.stem}")
        
        choice = Prompt.ask("Select preset", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                with open(presets[idx]) as f:
                    config = json.load(f)
                
                self.session.models = [ModelSlot(**m) for m in config.get("models", [])]
                self.session.rounds = config.get("rounds", 5)
                self.session.paradigm = config.get("paradigm", "relay")
                self.session.initial_prompt = config.get("initial_prompt", "")
                self.session.infinite = config.get("infinite", False)
                self.session.summarize_every = config.get("summarize_every", 0)
                
                # Load topology
                if "topology" in config:
                    self.session.topology = TopologyConfig(**config["topology"])
                
                # Load stop conditions
                if "stop_conditions" in config:
                    self.session.stop_conditions = StopConditions(**config["stop_conditions"])
                
                self.selected_model_idx = 0
                self.status_message = f"Loaded: {presets[idx].stem}"
        except (ValueError, json.JSONDecodeError) as e:
            self.status_message = f"Load error: {e}"
    
    def import_from_url(self):
        """Import configuration from a Dreams of Electric Mind URL."""
        console.clear()
        console.print("[bold magenta]Import from Infinite Backrooms[/]\n")
        console.print("[dim]Paste a URL from dreams-of-an-electric-mind.webflow.io[/]")
        console.print("[dim]Example: https://dreams-of-an-electric-mind.webflow.io/dreams/conversation-xxx[/]\n")
        
        url = Prompt.ask("URL", default="")
        if not url:
            self.status_message = "Import cancelled"
            return
        
        console.print("\n[yellow]Fetching configuration...[/]")
        
        try:
            from src.cli.backrooms_importer import fetch_backrooms_url, convert_to_crosstalk_session
            
            # Run async fetch
            config = asyncio.run(fetch_backrooms_url(url))
            
            if not config:
                self.status_message = "Could not parse configuration from URL"
                input("\nPress Enter to continue...")
                return
            
            # Convert to our session format
            session_data = convert_to_crosstalk_session(config)
            
            # Apply to current session
            self.session.models = session_data["models"]
            self.session.initial_prompt = session_data.get("initial_prompt", "")
            self.session.paradigm = session_data.get("paradigm", "relay")
            self.session.rounds = session_data.get("rounds", 10)
            self.selected_model_idx = 0
            
            console.print(f"\n[green]✓ Imported {len(config.actors)} actors from {config.scenario_name}[/]")
            for i, actor in enumerate(config.actors):
                console.print(f"  AI{i+1}: {actor.name} → {actor.model_id}")
            
            self.status_message = f"Imported: {config.scenario_name}"
            input("\nPress Enter to continue...")
            
        except ImportError as e:
            console.print(f"[red]Import module not found: {e}[/]")
            input("\nPress Enter to continue...")
        except Exception as e:
            console.print(f"[red]Import error: {e}[/]")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to continue...")
    
    def run_session(self):
        """Execute the crosstalk session."""
        if not self.session.initial_prompt:
            self.status_message = "Set initial prompt first [P]"
            return
        
        console.clear()
        console.print(Panel(
            "[bold yellow]Starting Crosstalk Session...[/]\n\n"
            f"Models: {len(self.session.models)}\n"
            f"Rounds: {self.session.rounds}\n"
            f"Paradigm: {self.session.paradigm}",
            title="🔮 RUNNING",
            border_style="yellow"
        ))
        
        # Import and run the engine
        try:
            from src.cli.crosstalk_engine import run_crosstalk
            asyncio.run(run_crosstalk(self.session))
        except ImportError:
            console.print("[red]Crosstalk engine not found. Creating placeholder...[/]")
            input("\nPress Enter to continue...")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            input("\nPress Enter to continue...")
    
    def run(self):
        """Main loop."""
        while self.running:
            try:
                self.draw()
                self.handle_input()
            except KeyboardInterrupt:
                self.running = False
        
        console.clear()
        console.print("[dim]Crosstalk Studio closed.[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Entry point for Crosstalk Studio."""
    try:
        studio = CrosstalkStudio()
        studio.run()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
