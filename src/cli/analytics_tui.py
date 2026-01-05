#!/usr/bin/env python3
"""
Analytics Configurator & Viewer TUI

Unified interface for:
1. Enabling/disabling usage tracking
2. Viewing comprehensive analytics
3. Exporting data
4. Managing analytics settings
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt, Confirm

from src.cli.env_utils import update_env_values, get_env_value
from src.services.usage.usage_tracker import UsageTracker

console = Console()


class AnalyticsConfigurator:
    """Analytics configuration and viewing TUI."""

    def __init__(self):
        self.running = True
        self.usage_tracker = UsageTracker()

    def draw_header(self):
        """Draw the header."""
        # Check status
        track_usage = get_env_value("TRACK_USAGE", "false").lower() == "true"
        status_color = "green" if track_usage else "yellow"
        status_text = "ENABLED" if track_usage else "DISABLED"
        tracking_status = f"[{status_color}]{status_text}[/{status_color}]"

        console.print(Panel(
            f"[bold cyan]📊 Analytics Configurator & Viewer[/]\n\n"
            f"[dim]Track, analyze, and optimize your API usage[/]\n"
            f"Tracking Status: {tracking_status}",
            box=box.DOUBLE,
            style="cyan",
            padding=(1, 2),
            expand=False
        ))

    def draw_menu(self):
        """Draw the main menu."""
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
        table.add_column("", width=3)
        table.add_column("Option", width=35)
        table.add_column("Description", width=35)

        options = [
            ("1", "🚀 Enable/Disable Tracking", "Turn usage tracking on/off"),
            ("2", "📈 View Summary (7d)", "Quick stats overview"),
            ("3", "💰 Smart Routing Savings", "Cost optimization analysis"),
            ("4", "🔧 Token Breakdown", "Detailed token composition"),
            ("5", "🏢 Provider Performance", "Provider comparison"),
            ("6", "📊 Model Comparison", "Model efficiency stats"),
            ("7", "💡 AI Insights", "Personalized recommendations"),
            ("8", "📤 Export Data", "CSV/JSON export"),
            ("9", "🔮 Full Analytics Dashboard", "View ALL analytics"),
            ("0", "🚪 Exit", "Return to settings")
        ]

        for marker, label, desc in options:
            table.add_row(marker, label, desc)

        console.print(table)

    def draw(self):
        """Draw the full screen."""
        console.clear()
        self.draw_header()
        console.print()
        self.draw_menu()

    def handle_input(self):
        """Handle keyboard input."""
        choice = Prompt.ask("\n→ Select option", default="0").strip()
        return choice

    def toggle_tracking(self):
        """Toggle TRACK_USAGE setting."""
        current = get_env_value("TRACK_USAGE", "false").lower() == "true"
        new_value = "false" if current else "true"

        console.print(f"\n[yellow]Current status: {'ENABLED' if current else 'DISABLED'}[/yellow]")

        if Confirm.ask(f"Turn usage tracking {'OFF' if current else 'ON'}?"):
            update_env_values({"TRACK_USAGE": new_value}, verbose=True)
            # Update runtime environment
            os.environ["TRACK_USAGE"] = new_value

            if new_value == "true":
                console.print("\n[green]✓ Usage tracking ENABLED[/green]")
                console.print("[dim]   Note: Restart proxy to start collecting data[/dim]")
            else:
                console.print("\n[yellow]○ Usage tracking DISABLED[/yellow]")

            input("\nPress Enter to continue...")

    def check_tracking_enabled(self) -> bool:
        """Check if tracking is enabled and show warning if not."""
        enabled = self.usage_tracker.enabled
        if not enabled:
            console.print("\n[bold red]⚠️  Usage tracking is DISABLED[/bold red]")
            console.print("[yellow]   Enable it first to view analytics[/yellow]")
            console.print("[dim]   Option 1: Enable tracking[/dim]")
            input("\nPress Enter to continue...")
        return enabled

    def view_summary(self):
        """View cost summary."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        console.clear()
        console.print(Panel(
            f"[bold cyan]📊 Cost Summary (Last {days} Days)[/]",
            border_style="cyan"
        ))

        summary = self.usage_tracker.get_cost_summary(days=days)
        top_models = self.usage_tracker.get_top_models(limit=10)

        if not summary:
            console.print("\n[dim]No data available yet.[/dim]")
            input("\nPress Enter to continue...")
            return

        # Display summary
        console.print(f"\n[bold yellow]Overview:[/bold yellow]")
        console.print(f"  Total Requests: {summary.get('total_requests', 0):,}")
        console.print(f"  Total Tokens: {summary.get('total_tokens', 0):,}")
        console.print(f"    - Input: {summary.get('total_input_tokens', 0):,}")
        console.print(f"    - Output: {summary.get('total_output_tokens', 0):,}")
        console.print(f"    - Thinking: {summary.get('total_thinking_tokens', 0):,}")
        console.print(f"  Estimated Cost: ${summary.get('total_cost', 0.0):.4f}")
        console.print(f"  Avg Duration: {summary.get('avg_duration_ms', 0.0):.0f}ms")
        console.print(f"  Avg Speed: {summary.get('avg_tokens_per_second', 0.0):.0f} tokens/sec")

        if top_models:
            console.print(f"\n[bold cyan]Top Models:[/bold cyan]")
            for i, model in enumerate(top_models[:5], 1):
                console.print(f"  {i}. {model['model'][:40]} - {model['request_count']} reqs")

        input("\nPress Enter to continue...")

    def view_savings(self):
        """View smart routing savings."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        console.clear()
        console.print(Panel(
            f"[bold green]💰 Smart Routing Savings (Last {days} Days)[/]",
            border_style="green"
        ))

        savings = self.usage_tracker.get_savings_data(days=days)

        if not savings:
            console.print("\n[dim]No savings data available yet.[/dim]")
            console.print("[dim]Savings are tracked when original_cost differs from actual cost.[/dim]")
            input("\nPress Enter to continue...")
            return

        total_savings = sum(s['total_savings'] for s in savings)

        console.print(f"\n[bold yellow]Total Savings: ${total_savings:.4f}[/bold yellow]")

        print(f"\n{'Route':<50} {'Reqs':<8} {'Savings':<12} {'Avg %'}")
        print("-" * 85)

        for saving in savings:
            route = f"{saving['original_model'][:20]} → {saving['routed_model'][:20]}"
            reqs = saving['request_count']
            savings_amt = f"${saving['total_savings']:.4f}"
            pct = f"{saving['avg_savings_percent']:.1f}%"

            print(f"{route:<50} {reqs:<8} {savings_amt:<12} {pct}")

        input("\nPress Enter to continue...")

    def view_token_breakdown(self):
        """View detailed token breakdown."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        console.clear()
        console.print(Panel(
            f"[bold magenta]🔧 Token Composition (Last {days} Days)[/]",
            border_style="magenta"
        ))

        stats = self.usage_tracker.get_token_breakdown_stats(days=days)

        if not stats:
            console.print("\n[dim]No token breakdown data available yet.[/dim]")
            input("\nPress Enter to continue...")
            return

        console.print(f"\n[bold yellow]Total: {stats['total_tokens']:,} tokens in {stats['request_count']} requests[/bold yellow]")

        types = [
            ('prompt', 'Prompt'),
            ('completion', 'Completion'),
            ('reasoning', 'Reasoning'),
            ('cached', 'Cached'),
            ('tool_use', 'Tool Use'),
            ('audio', 'Audio')
        ]

        for key, label in types:
            if key in stats and stats[key]['absolute'] > 0:
                data = stats[key]
                pct = data['percentage']
                abs_val = data['absolute']

                # Visual bar
                bar_length = int(pct / 2)
                bar = "█" * bar_length

                console.print(f"  [cyan]{label.ljust(12)}[/cyan]: {pct:5.1f}% | {bar} {abs_val:,} tokens")

        input("\nPress Enter to continue...")

    def view_providers(self):
        """View provider performance."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        console.clear()
        console.print(Panel(
            f"[bold blue]🏢 Provider Performance (Last {days} Days)[/]",
            border_style="blue"
        ))

        providers = self.usage_tracker.get_provider_stats(days=days)

        if not providers:
            console.print("\n[dim]No provider data available yet.[/dim]")
            input("\nPress Enter to continue...")
            return

        print(f"\n{'Provider':<18} {'Reqs':<6} {'Tokens':<9} {'Cost':<10} {'$/1K':<8} {'Latency'}")
        print("-" * 80)

        for p in providers:
            name = p['provider'][:16]
            reqs = p['total_requests']
            tokens = f"{p['total_tokens']/1000:.0f}k" if p['total_tokens'] >= 1000 else str(p['total_tokens'])
            cost = f"${p['total_cost']:.2f}"
            per_k = f"${p['avg_cost_per_1k_tokens']:.3f}"
            latency = f"{p['avg_duration_ms']:.0f}ms"

            print(f"{name:<18} {reqs:<6} {tokens:<9} {cost:<10} {per_k:<8} {latency}")

        input("\nPress Enter to continue...")

    def view_model_comparison(self):
        """View model comparison."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        min_reqs = Prompt.ask("Min requests per model", default="1").strip()
        try:
            min_reqs = int(min_reqs)
        except ValueError:
            min_reqs = 1

        console.clear()
        console.print(Panel(
            f"[bold yellow]📊 Model Comparison (Last {days} Days)[/]",
            border_style="yellow"
        ))

        models = self.usage_tracker.get_model_comparison(days=days)
        filtered = [m for m in models if m['total_requests'] >= min_reqs]

        if not filtered:
            console.print("\n[dim]No model comparison data available yet.[/dim]")
            input("\nPress Enter to continue...")
            return

        print(f"\n{'Model':<32} {'Reqs':<6} {'Tok/Req':<9} {'$/1K':<8} {'Latency':<8} {'Tools'}")
        print("-" * 80)

        for m in filtered:
            name = m['model'][:30]
            reqs = m['total_requests']
            tok_per_req = f"{m['avg_tokens_per_request']:.0f}"
            per_k = f"${m['avg_cost_per_1k_tokens']:.2f}"
            latency = f"{m['avg_duration_ms']:.0f}ms"
            tools = m['tool_requests']

            # Color code cost
            if m['avg_cost_per_1k_tokens'] < 5:
                per_k = f"[green]{per_k}[/green]"
            elif m['avg_cost_per_1k_tokens'] < 10:
                per_k = f"[yellow]{per_k}[/yellow]"
            else:
                per_k = f"[red]{per_k}[/red]"

            console.print(f"{name:<32} {reqs:<6} {tok_per_req:<9} {per_k:<8} {latency:<8} {tools}")

        input("\nPress Enter to continue...")

    def view_insights(self):
        """View AI insights."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        console.clear()
        console.print(Panel(
            f"[bold magenta]💡 AI Insights & Recommendations (Last {days} Days)[/]",
            border_style="magenta"
        ))

        # Get dashboard data for insight generation
        data = self.usage_tracker.get_dashboard_summary(days=days)

        if not data or not data.get('summary'):
            console.print("\n[dim]No data available for insights.[/dim]")
            input("\nPress Enter to continue...")
            return

        # Generate insights (same logic as CLI analytics)
        insights = []

        # Savings
        total_savings = sum(s['total_savings'] for s in data.get('savings', []))
        if total_savings > 0:
            top_saving = max(data.get('savings', []), key=lambda x: x['total_savings']) if data.get('savings') else None
            if top_saving:
                insights.append(("💰 Cost Savings", f"Saved ${total_savings:.4f} ({top_saving['avg_savings_percent']:.1f}%) by routing {top_saving['request_count']} requests", "HIGH" if top_saving['avg_savings_percent'] > 20 else "MED"))

        # Token efficiency
        token_bd = data.get('token_breakdown', {})
        if token_bd and token_bd.get('total_tokens', 0) > 0:
            reasoning_pct = token_bd.get('reasoning', {}).get('percentage', 0)
            if reasoning_pct > 30:
                insights.append(("⚡ High Reasoning Usage", f"{reasoning_pct:.1f}% tokens are reasoning. Consider simpler prompts", "MED"))

            cached_pct = token_bd.get('cached', {}).get('percentage', 0)
            if cached_pct < 5:
                insights.append(("🔄 Low Cache Utilization", f"Only {cached_pct:.1f}% cached. Use prompt caching", "LOW"))

        # Provider concentration
        providers = data.get('providers', [])
        if len(providers) > 1:
            top_p = providers[0]
            second_p = providers[1]
            if top_p['total_cost'] > second_p['total_cost'] * 2:
                pct = (top_p['total_cost'] / (top_p['total_cost'] + second_p['total_cost']) * 100)
                insights.append(("🏢 Provider Concentration", f"{top_p['provider']} is {pct:.1f}% of costs", "LOW"))

        # Performance
        if data['summary'].get('avg_duration_ms', 0) > 5000:
            insights.append(("⏱️ High Latency", f"Avg {data['summary']['avg_duration_ms']:.0f}ms. Try faster models", "MED"))

        # Model efficiency
        models = data.get('models', [])
        if len(models) > 3:
            inefficient = [m for m in models if m['avg_cost_per_1k_tokens'] > 10 and m['total_requests'] > 10]
            if inefficient:
                top_ineff = inefficient[0]
                insights.append(("📊 Expensive Models", f"{top_ineff['model']} costs ${top_ineff['avg_cost_per_1k_tokens']:.2f}/1K", "MED"))

        console.print(f"\n[bold cyan]{len(insights)} Insights Found:[/bold cyan]\n")

        for i, (title, desc, priority) in enumerate(insights, 1):
            priority_color = "red" if priority == "HIGH" else "yellow" if priority == "MED" else "cyan"
            console.print(f"  {i}. [bold]{title}[/bold] [{priority_color}]{priority}[/{priority_color}]")
            console.print(f"     {desc}\n")

        input("\nPress Enter to continue...")

    def export_data(self):
        """Export analytics data."""
        if not self.check_tracking_enabled():
            return

        console.print("\n[cyan]Export Options:[/cyan]")
        console.print("  1. CSV format")
        console.print("  2. JSON format")

        choice = Prompt.ask("\nSelect format", choices=["1", "2"], default="1")

        filename = Prompt.ask("\nFilename (default: analytics_export)", default="analytics_export").strip()
        if choice == "1":
            filename += ".csv"
            fmt = "csv"
        else:
            filename += ".json"
            fmt = "json"

        days = Prompt.ask("Days of data (default: 30)", default="30").strip()
        try:
            days = int(days)
        except ValueError:
            days = 30

        console.print(f"\n[yellow]Exporting {fmt} data to {filename}...[/yellow]")

        if fmt == "csv":
            success = self.usage_tracker.export_to_csv(filename, days=days)
        else:
            success = self.usage_tracker.export_to_json(filename, days=days)

        if success:
            console.print(f"[green]✓ Export successful: {filename}[/green]")
        else:
            console.print(f"[red]✗ Export failed[/red]")

        input("\nPress Enter to continue...")

    def full_dashboard(self):
        """Display all analytics."""
        if not self.check_tracking_enabled():
            return

        days = Prompt.ask("\nDays to analyze", default="7").strip()
        try:
            days = int(days)
        except ValueError:
            days = 7

        console.clear()
        console.print(Panel(
            f"[bold white]🔮 Full Analytics Dashboard (Last {days} Days)[/]",
            border_style="white"
        ))

        # Run the existing analytics script
        try:
            # Temporarily call each display function
            from src.cli.analytics import (
                display_top_models, display_cost_summary, display_savings_analysis,
                display_token_breakdown, display_provider_stats, display_model_comparison,
                display_json_toon_analysis, display_ai_insights
            )

            # Set days for internal use (modify the tracker temporarily)
            self.usage_tracker.get_dashboard_summary(days=days)

            # Display all sections
            display_top_models()
            display_cost_summary()
            display_savings_analysis()
            display_token_breakdown()
            display_provider_stats()
            display_model_comparison()
            display_json_toon_analysis()
            display_ai_insights()

        except Exception as e:
            console.print(f"[red]Error displaying dashboard: {e}[/red]")

        input("\nPress Enter to continue...")

    def run(self):
        """Main loop."""
        while self.running:
            self.draw()
            choice = self.handle_input()

            if choice == "0":
                self.running = False
            elif choice == "1":
                self.toggle_tracking()
            elif choice == "2":
                self.view_summary()
            elif choice == "3":
                self.view_savings()
            elif choice == "4":
                self.view_token_breakdown()
            elif choice == "5":
                self.view_providers()
            elif choice == "6":
                self.view_model_comparison()
            elif choice == "7":
                self.view_insights()
            elif choice == "8":
                self.export_data()
            elif choice == "9":
                self.full_dashboard()
            else:
                console.print("\n[red]Invalid option[/red]")
                input("Press Enter to continue...")


def main():
    """Entry point."""
    try:
        configurator = AnalyticsConfigurator()
        configurator.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Analytics closed.[/dim]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()