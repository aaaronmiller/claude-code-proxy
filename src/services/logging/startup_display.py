"""Colorful startup configuration display."""

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from src.services.usage.model_limits import get_model_limits


def display_startup_config(config):
    """
    Display comprehensive startup configuration with colors.
    
    Color scheme:
    - Cyan/Blue: Primary info (calm, professional)
    - Magenta/Purple: Highlights and important values
    - Green: Success/enabled features
    - Yellow: Warnings
    - Dim: Secondary info
    """
    if not RICH_AVAILABLE:
        _display_plain(config)
        return
    
    console = Console()
    
    # Header
    console.print()
    console.print("🚀 [bold bright_cyan]The Ultimate Proxy[/bold bright_cyan] [dim]v2.1.0[/dim]")
    console.print()
    
    # Provider Configuration
    provider_table = Table(show_header=False, box=None, padding=(0, 2))
    provider_table.add_column("Key", style="dim")
    provider_table.add_column("Value", style="bright_cyan")

    provider_name = _extract_provider_name(config.openai_base_url)
    provider_table.add_row("Provider", f"[bold]{provider_name}[/bold]")
    provider_table.add_row("Endpoint", config.openai_base_url)

    # Show API key status (with semantic naming hint)
    if config.openai_api_key:
        key_preview = config.openai_api_key[:15] + "..." if len(config.openai_api_key) > 15 else config.openai_api_key
        provider_table.add_row("Provider Key", f"[green]{key_preview}[/green]")
    else:
        provider_table.add_row("Provider Key", "[yellow]NOT SET (passthrough mode)[/yellow]")

    console.print(Panel(provider_table, title="[bold magenta]Provider[/bold magenta]", border_style="cyan"))
    
    # Model Configuration with Context Windows and Provider
    model_table = Table(show_header=True, box=None, padding=(0, 1))
    model_table.add_column("Tier", style="dim", width=8)
    model_table.add_column("Provider", style="yellow", width=12)
    model_table.add_column("Model", style="bright_cyan", width=35)
    model_table.add_column("Context", style="green", justify="right", width=10)
    model_table.add_column("Output", style="blue", justify="right", width=10)
    
    for tier, model in [("BIG", config.big_model), ("MIDDLE", config.middle_model), ("SMALL", config.small_model)]:
        context, output = get_model_limits(model)
        ctx_str = _format_tokens(context) if context > 0 else "unknown"
        out_str = _format_tokens(output) if output > 0 else "unknown"
        
        # Extract provider from model prefix or detect from default endpoint
        provider = _extract_model_provider(model, config.openai_base_url)
        model_display = model.split('/', 1)[-1] if '/' in model else model
        
        model_table.add_row(tier, provider, model_display, ctx_str, out_str)
    
    console.print(Panel(model_table, title="[bold magenta]Models[/bold magenta]", border_style="cyan"))
    
    # Reasoning Configuration
    if config.reasoning_effort or config.reasoning_max_tokens or config.verbosity:
        reasoning_table = Table(show_header=False, box=None, padding=(0, 2))
        reasoning_table.add_column("Setting", style="dim")
        reasoning_table.add_column("Value", style="bright_magenta")
        
        if config.reasoning_effort:
            reasoning_table.add_row("Effort", config.reasoning_effort.upper())
        if config.reasoning_max_tokens:
            reasoning_table.add_row("Max Tokens", _format_tokens(config.reasoning_max_tokens))
        if config.verbosity:
            reasoning_table.add_row("Verbosity", config.verbosity)
        reasoning_table.add_row("Exclude", "Yes" if config.reasoning_exclude else "No")
        
        console.print(Panel(reasoning_table, title="[bold magenta]Reasoning[/bold magenta]", border_style="cyan"))
    
    # Hybrid Mode (if enabled)
    hybrid_enabled = config.enable_big_endpoint or config.enable_middle_endpoint or config.enable_small_endpoint
    if hybrid_enabled:
        hybrid_table = Table(show_header=True, box=None, padding=(0, 1))
        hybrid_table.add_column("Tier", style="dim", width=8)
        hybrid_table.add_column("Endpoint", style="bright_cyan", width=50)
        
        if config.enable_big_endpoint:
            hybrid_table.add_row("BIG", config.big_endpoint)
        if config.enable_middle_endpoint:
            hybrid_table.add_row("MIDDLE", config.middle_endpoint)
        if config.enable_small_endpoint:
            hybrid_table.add_row("SMALL", config.small_endpoint)
        
        console.print(Panel(hybrid_table, title="[bold magenta]Model Routing[/bold magenta]", border_style="cyan"))
    
    # Server Settings
    server_table = Table(show_header=False, box=None, padding=(0, 2))
    server_table.add_column("Setting", style="dim")
    server_table.add_column("Value", style="bright_cyan")
    
    server_table.add_row("Host", config.host)
    server_table.add_row("Port", str(config.port))
    server_table.add_row("Log Level", config.log_level.split()[0].upper())
    server_table.add_row("Timeout", f"{config.request_timeout}s")
    server_table.add_row("Max Tokens", _format_tokens(config.max_tokens_limit))

    auth_status = "[green]Enabled[/green]" if config.anthropic_api_key else "[dim]Disabled[/dim]"
    server_table.add_row("Proxy Auth", auth_status)
    
    console.print(Panel(server_table, title="[bold magenta]Server[/bold magenta]", border_style="cyan"))
    
    # Quick Tips - Grouped by Category
    tips_table = Table(show_header=True, box=None, padding=(0, 2))
    tips_table.add_column("Category", style="dim", width=14)
    tips_table.add_column("Command", style="yellow", width=45)
    
    # Most used commands
    tips_table.add_row("Settings", "--settings (unified TUI)")
    tips_table.add_row("Models", "--select-models  |  --set-big MODEL")
    tips_table.add_row("Diagnostics", "--doctor  |  --config  |  --analytics")
    tips_table.add_row("Crosstalk", "--crosstalk-studio  |  --crosstalk MODEL1,MODEL2")
    tips_table.add_row("Help", "-h  |  --help")

    console.print(Panel(tips_table, title="[bold green]CLI Arguments[/bold green]", border_style="cyan"))
    
    # Endpoints
    console.print()
    console.print(f"[dim]→ API Endpoint[/dim]  [bold bright_cyan]http://{config.host}:{config.port}/v1[/bold bright_cyan]")
    console.print(f"[dim]→ Web Dashboard[/dim] [bold bright_cyan]http://{config.host}:{config.port}/[/bold bright_cyan]")
    console.print(f"[dim]→ Full help[/dim]     [yellow]python start_proxy.py --help[/yellow]")
    console.print()


def _display_plain(config):
    """Plain text fallback without Rich."""
    print()
    print("🚀 Claude Code Proxy v1.0.0")
    print()
    print("Provider:")
    print(f"  {_extract_provider_name(config.openai_base_url)}")
    print(f"  {config.openai_base_url}")
    # Show API key status (with semantic naming hint)
    if config.openai_api_key:
        key_preview = config.openai_api_key[:15] + "..." if len(config.openai_api_key) > 15 else config.openai_api_key
        print(f"  Provider Key: {key_preview}")
    else:
        print(f"  Provider Key: NOT SET (passthrough mode)")
    print()
    print("Models:")
    for tier, model in [("BIG", config.big_model), ("MIDDLE", config.middle_model), ("SMALL", config.small_model)]:
        context, output = get_model_limits(model)
        ctx_str = _format_tokens(context) if context > 0 else "unknown"
        out_str = _format_tokens(output) if output > 0 else "unknown"
        print(f"  {tier:8} {model:40} CTX:{ctx_str:>8} OUT:{out_str:>8}")
    print()
    if config.reasoning_effort or config.reasoning_max_tokens:
        print("Reasoning:")
        if config.reasoning_effort:
            print(f"  Effort: {config.reasoning_effort.upper()}")
        if config.reasoning_max_tokens:
            print(f"  Max Tokens: {_format_tokens(config.reasoning_max_tokens)}")
        print()
    print(f"Server: http://{config.host}:{config.port}")
    print()


def _extract_provider_name(base_url: str) -> str:
    """Extract provider name from base URL."""
    if "openrouter" in base_url:
        return "OpenRouter"
    elif "openai.com" in base_url:
        return "OpenAI"
    elif "azure" in base_url:
        return "Azure OpenAI"
    elif "googleapis.com" in base_url:
        return "Google Gemini"
    elif "localhost" in base_url or "127.0.0.1" in base_url:
        if "8317" in base_url:
            return "VibeProxy/Gemini (Local)"
        elif "11434" in base_url:
            return "Ollama (Local)"
        elif "1234" in base_url:
            return "LMStudio (Local)"
        return "Local"
    return "Custom"


def _extract_model_provider(model_name: str, default_base_url: str) -> str:
    """Extract provider from model name prefix or detect from default endpoint.
    
    Args:
        model_name: Model name, possibly with provider prefix (e.g., "vibeproxy/gemini-2.5-pro")
        default_base_url: Default API endpoint URL
        
    Returns:
        Provider name (e.g., "VibeProxy", "OpenRouter", "OpenAI")
    """
    # If model has a provider prefix, extract it
    if "/" in model_name:
        prefix = model_name.split("/", 1)[0].lower()
        provider_map = {
            "vibeproxy": "VibeProxy",
            "antigravity": "VibeProxy",
            "openrouter": "OpenRouter",
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google",
            "meta-llama": "Meta",
            "mistral": "Mistral",
            "cohere": "Cohere",
            "qwen": "Qwen",
        }
        return provider_map.get(prefix, prefix.title())
    
    # No prefix - detect from default endpoint
    if "openrouter" in default_base_url:
        return "OpenRouter"
    elif "8317" in default_base_url:
        return "VibeProxy"
    elif "openai.com" in default_base_url:
        return "OpenAI"
    elif "googleapis" in default_base_url:
        return "Google"
    elif "11434" in default_base_url:
        return "Ollama"
    else:
        return "Default"


def _format_tokens(count: int) -> str:
    """Format token count compactly."""
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.0f}k"
    return str(count)

# Alias for backward compatibility
print_startup_banner = display_startup_config
