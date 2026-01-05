#!/usr/bin/env python3
"""
Usage Analytics Viewer

View actual API usage statistics from tracked requests.
Requires TRACK_USAGE=true to be enabled.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.usage.usage_tracker import usage_tracker
from src.services.usage.cost_calculator import calculate_cost


# ANSI Colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_RED = "\033[91m"


def color(text: str, color_code: str) -> str:
    """Apply color to text."""
    return f"{color_code}{text}{Colors.RESET}"


def display_header(title: str):
    """Display section header."""
    print("\n" + "="*70)
    print(color(f"  {title}", Colors.BOLD + Colors.CYAN))
    print("="*70)


def display_top_models():
    """Display most used models."""
    display_header("📊 Top Models by Request Count")

    models = usage_tracker.get_top_models(limit=15)

    if not models:
        print(color("  No usage data available.", Colors.DIM))
        print(color("  Enable tracking with TRACK_USAGE=true", Colors.YELLOW))
        return

    print("\n" + color(f"{'Rank':<6}{'Model':<45}{'Requests':<12}{'Total Tokens':<15}{'Avg Cost'}", Colors.BOLD))
    print(color("-" * 100, Colors.DIM))

    for i, model in enumerate(models, 1):
        model_name = model['model'][:43]
        requests = model['request_count']
        total_tokens = model['total_input_tokens'] + model['total_output_tokens']
        avg_cost = model['total_cost'] / requests if requests > 0 else 0.0

        # Format numbers
        tokens_str = f"{total_tokens/1000:.1f}k" if total_tokens >= 1000 else str(total_tokens)
        cost_str = f"${avg_cost:.4f}"

        # Color code by usage
        if i == 1:
            rank_color = Colors.BRIGHT_GREEN
        elif i <= 3:
            rank_color = Colors.GREEN
        elif i <= 5:
            rank_color = Colors.CYAN
        else:
            rank_color = ""

        print(f"{color(f'#{i}', rank_color):<13}{model_name:<45}{requests:<12}{tokens_str:<15}{cost_str}")


def display_cost_summary():
    """Display cost summary."""
    display_header("💰 Cost Summary (Last 7 Days)")

    summary = usage_tracker.get_cost_summary(days=7)

    if not summary:
        print(color("  No cost data available.", Colors.DIM))
        return

    print()
    print(f"  {color('Total Requests:', Colors.CYAN)} {summary.get('total_requests', 0):,}")
    print(f"  {color('Total Tokens:', Colors.CYAN)} {summary.get('total_tokens', 0):,}")
    print(f"    - {color('Input:', Colors.GREEN)} {summary.get('total_input_tokens', 0):,}")
    print(f"    - {color('Output:', Colors.BLUE)} {summary.get('total_output_tokens', 0):,}")
    print(f"    - {color('Thinking:', Colors.MAGENTA)} {summary.get('total_thinking_tokens', 0):,}")
    print()

    total_cost = summary.get('total_cost', 0.0)
    cost_color = Colors.GREEN if total_cost < 1.0 else Colors.YELLOW if total_cost < 10.0 else Colors.RED
    print(f"  {color('Estimated Cost:', Colors.BRIGHT_CYAN)} {color(f'${total_cost:.2f}', cost_color)}")

    print()
    print(f"  {color('Performance:', Colors.CYAN)}")
    print(f"    - Avg Duration: {summary.get('avg_duration_ms', 0.0):.0f}ms")
    print(f"    - Avg Speed: {summary.get('avg_tokens_per_second', 0.0):.0f} tokens/sec")


def display_json_toon_analysis():
    """Display JSON/TOON analysis."""
    display_header("🔍 JSON → TOON Conversion Analysis")

    analysis = usage_tracker.get_json_toon_analysis()

    if not analysis:
        print(color("  No JSON analysis data available.", Colors.DIM))
        return

    total_requests = analysis.get('total_requests', 0)
    json_requests = analysis.get('json_requests', 0)
    json_pct = analysis.get('json_percentage', 0.0)

    print()
    print(f"  {color('Total Requests:', Colors.CYAN)} {total_requests:,}")
    print(f"  {color('JSON Requests:', Colors.CYAN)} {json_requests:,} ({json_pct:.1f}%)")
    print(f"  {color('Total JSON:', Colors.CYAN)} {analysis.get('total_json_bytes', 0):,} bytes")
    print(f"  {color('Avg JSON Size:', Colors.CYAN)} {analysis.get('avg_json_size', 0):.0f} bytes")
    print()

    savings = analysis.get('estimated_toon_savings_bytes', 0)
    savings_tokens = savings // 4  # Rough estimate: 4 bytes per token

    savings_color = Colors.GREEN if savings_tokens > 1000 else Colors.YELLOW
    print(f"  {color('Est. TOON Savings:', Colors.BRIGHT_CYAN)} {color(f'~{savings:,} bytes (~{savings_tokens:,} tokens)', savings_color)}")

    print()
    recommended = analysis.get('recommended', False)
    if recommended:
        print(color("  ✅ TOON conversion RECOMMENDED", Colors.BRIGHT_GREEN))
        print(color("     High JSON usage detected - TOON could save significant tokens", Colors.GREEN))
    else:
        print(color("  ℹ️  TOON conversion not needed yet", Colors.CYAN))
        if json_pct < 30:
            print(color(f"     Low JSON usage ({json_pct:.1f}% < 30%)", Colors.DIM))
        if analysis.get('avg_json_size', 0) < 500:
            print(color(f"     Small JSON payloads (avg {analysis.get('avg_json_size', 0):.0f} < 500 bytes)", Colors.DIM))


def export_to_csv():
    """Export usage data to CSV."""
    display_header("📤 Export to CSV")

    filename = input(color("\nEnter filename (default: usage_export.csv): ", Colors.BRIGHT_CYAN)).strip()
    if not filename:
        filename = "usage_export.csv"

    if not filename.endswith('.csv'):
        filename += '.csv'

    days = input(color("Days of data to export (default: 30): ", Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 30
    except ValueError:
        days = 30

    if usage_tracker.export_to_csv(filename, days=days):
        print(color(f"\n✓ Exported to {filename}", Colors.BRIGHT_GREEN))
    else:
        print(color(f"\n✗ Export failed", Colors.BRIGHT_RED))


def display_savings_analysis():
    """Display smart routing savings analysis."""
    display_header("💰 Smart Routing Savings Analysis")

    days = input(color("\nDays to analyze (default: 7): ", Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7

    savings_data = usage_tracker.get_savings_data(days=days)

    if not savings_data:
        print(color("  No savings data available.", Colors.DIM))
        print(color("  Savings are tracked when original_cost differs from actual cost.", Colors.YELLOW))
        return

    total_savings = sum(s['total_savings'] for s in savings_data)
    avg_savings = sum(s['avg_savings_percent'] for s in savings_data) / len(savings_data) if savings_data else 0

    print(f"\n  {color('Total Savings:', Colors.BRIGHT_CYAN)} {color(f'${total_savings:.4f}', Colors.BRIGHT_GREEN)}")
    print(f"  {color('Avg Savings:', Colors.BRIGHT_CYAN)} {color(f'{avg_savings:.1f}%', Colors.BRIGHT_GREEN)}")
    print()

    print(color(f"{'Route':<50}{'Requests':<12}{'Savings':<15}{'Avg %'}", Colors.BOLD))
    print(color("-" * 90, Colors.DIM))

    for saving in savings_data:
        route = f"{saving['original_model'][:20]} → {saving['routed_model'][:20]}"
        requests = saving['request_count']
        savings = f"${saving['total_savings']:.4f}"
        pct = f"{saving['avg_savings_percent']:.1f}%"

        print(f"{route:<50}{requests:<12}{savings:<15}{pct}")


def display_token_breakdown():
    """Display detailed token breakdown."""
    display_header("🔧 Token Composition Analysis")

    days = input(color("\nDays to analyze (default: 7): ", Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7

    token_stats = usage_tracker.get_token_breakdown_stats(days=days)

    if not token_stats:
        print(color("  No token breakdown data available.", Colors.DIM))
        print(color("  Requires enhanced token tracking.", Colors.YELLOW))
        return

    total = token_stats.get('total_tokens', 0)
    req_count = token_stats.get('request_count', 0)

    print(f"\n  {color('Total Tokens:', Colors.BRIGHT_CYAN)} {total:,}")
    print(f"  {color('Request Count:', Colors.BRIGHT_CYAN)} {req_count:,}")
    print()

    print(color("Token Type Distribution:", Colors.BOLD))
    print()

    types = [
        ('prompt', 'Prompt'),
        ('completion', 'Completion'),
        ('reasoning', 'Reasoning'),
        ('cached', 'Cached'),
        ('tool_use', 'Tool Use'),
        ('audio', 'Audio')
    ]

    for key, label in types:
        if key in token_stats:
            data = token_stats[key]
            abs_val = data['absolute']
            pct = data['percentage']

            if abs_val > 0:
                # Visual bar
                bar_length = int(pct / 2)  # Scale to 50 chars max
                bar = "█" * bar_length
                if bar_length < 5:
                    bar = bar.ljust(5)

                bar_color = Colors.GREEN if pct >= 10 else Colors.YELLOW if pct >= 5 else Colors.CYAN

                print(f"  {color(label.ljust(12), Colors.CYAN)}: {color(f'{pct:5.1f}%', bar_color)} | {color(bar, bar_color)} {abs_val:,} tokens")


def display_provider_stats():
    """Display provider-level statistics."""
    display_header("🏢 Provider Performance Analysis")

    days = input(color("\nDays to analyze (default: 7): ", Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7

    providers = usage_tracker.get_provider_stats(days=days)

    if not providers:
        print(color("  No provider data available.", Colors.DIM))
        return

    print()

    print(color(f"{'Provider':<20}{'Requests':<10}{'Tokens':<12}{'Cost':<12}{'$/1K':<10}{'Latency'}", Colors.BOLD))
    print(color("-" * 95, Colors.DIM))

    for provider in providers:
        name = provider['provider'][:18]
        reqs = provider['total_requests']
        tokens = f"{provider['total_tokens']/1000:.0f}k" if provider['total_tokens'] >= 1000 else str(provider['total_tokens'])
        cost = f"${provider['total_cost']:.2f}"
        per_k = f"${provider['avg_cost_per_1k_tokens']:.3f}"
        latency = f"{provider['avg_duration_ms']:.0f}ms"

        print(f"{name:<20}{reqs:<10}{tokens:<12}{cost:<12}{per_k:<10}{latency}")


def display_model_comparison():
    """Display model comparison statistics."""
    display_header("📊 Model Performance Comparison")

    days = input(color("\nDays to analyze (default: 7): ", Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7

    min_reqs = input(color("Min requests per model (default: 1): ", Colors.BRIGHT_CYAN)).strip()
    try:
        min_reqs = int(min_reqs) if min_reqs else 1
    except ValueError:
        min_reqs = 1

    models = usage_tracker.get_model_comparison(days=days)
    filtered = [m for m in models if m['total_requests'] >= min_reqs]

    if not filtered:
        print(color("  No model comparison data available.", Colors.DIM))
        return

    print()

    print(color(f"{'Model':<35}{'Reqs':<6}{'Tok/Req':<10}{'$/1K':<9}{'Latency':<9}{'Tools'}", Colors.BOLD))
    print(color("-" * 90, Colors.DIM))

    for model in filtered:
        name = model['model'][:33]
        reqs = model['total_requests']
        tok_per_req = f"{model['avg_tokens_per_request']:.0f}"
        per_k = f"${model['avg_cost_per_1k_tokens']:.2f}"
        latency = f"{model['avg_duration_ms']:.0f}ms"
        tools = model['tool_requests']

        # Color coding for efficiency
        cost_color = Colors.GREEN if model['avg_cost_per_1k_tokens'] < 5 else Colors.YELLOW if model['avg_cost_per_1k_tokens'] < 10 else Colors.RED

        print(f"{name:<35}{reqs:<6}{tok_per_req:<10}{color(per_k, cost_color):<9}{latency:<9}{tools}")


def display_ai_insights():
    """Display AI-generated insights and recommendations."""
    display_header("💡 AI Insights & Recommendations")

    days = input(color("\nDays to analyze (default: 7): ", Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7

    insights_data = usage_tracker.get_dashboard_summary(days=days)

    if not insights_data:
        print(color("  No data available for insights.", Colors.DIM))
        return

    print()
    print("  " + color("Analyzing your usage patterns...", Colors.CYAN))
    print()

    # Extract key data
    summary = insights_data.get('summary', {})
    savings = insights_data.get('savings', [])
    token_breakdown = insights_data.get('token_breakdown', {})
    providers = insights_data.get('providers', [])
    models = insights_data.get('models', [])

    insights = []

    # Generate insights
    total_savings = sum(s['total_savings'] for s in savings)
    if total_savings > 0:
        top_saving = max(savings, key=lambda x: x['total_savings']) if savings else None
        if top_saving:
            priority = "HIGH" if top_saving['avg_savings_percent'] > 20 else "MED"
            insights.append((
                "💰 Cost Savings",
                f"Saved ${total_savings:.4f} ({top_saving['avg_savings_percent']:.1f}%) by routing {top_saving['request_count']} requests",
                priority
            ))

    # Token efficiency
    if token_breakdown and token_breakdown.get('total_tokens', 0) > 0:
        reasoning_pct = token_breakdown.get('reasoning', {}).get('percentage', 0)
        if reasoning_pct > 30:
            insights.append((
                "⚡ High Reasoning Usage",
                f"{reasoning_pct:.1f}% tokens are reasoning. Consider simpler prompts for cost savings",
                "MED"
            ))

        cached_pct = token_breakdown.get('cached', {}).get('percentage', 0)
        if cached_pct < 5:
            insights.append((
                "🔄 Low Cache Utilization",
                f"Only {cached_pct:.1f}% cached. Prompt caching could save costs",
                "LOW"
            ))

    # Provider insights
    if len(providers) > 1:
        top_provider = providers[0]
        second_provider = providers[1]
        if top_provider['total_cost'] > second_provider['total_cost'] * 2:
            pct = (top_provider['total_cost'] / (top_provider['total_cost'] + second_provider['total_cost']) * 100)
            insights.append((
                "🏢 Provider Concentration",
                f"{top_provider['provider']} is {pct:.1f}% of costs. Consider diversifying",
                "LOW"
            ))

    # Performance insights
    if summary.get('avg_duration_ms', 0) > 5000:
        insights.append((
            "⏱️ High Latency",
            f"Average {summary['avg_duration_ms']:.0f}ms. Try streaming or faster models",
            "MED"
        ))

    # Model efficiency
    if len(models) > 3:
        inefficient = [m for m in models if m['avg_cost_per_1k_tokens'] > 10 and m['total_requests'] > 10]
        if inefficient:
            top_ineff = inefficient[0]
            insights.append((
                "📊 Expensive Model Usage",
                f"{top_ineff['model']} costs ${top_ineff['avg_cost_per_1k_tokens']:.2f}/1K tokens",
                "MED"
            ))

    if not insights:
        print("  " + color("ℹ️  No specific insights available yet.", Colors.CYAN))
        print("  " + color("Keep tracking usage to generate personalized recommendations.", Colors.DIM))
        return

    print(f"  {color(f'{len(insights)} Insights Found:', Colors.BOLD + Colors.BRIGHT_CYAN)}\n")

    priority_colors = {
        "HIGH": Colors.BRIGHT_RED,
        "MED": Colors.BRIGHT_YELLOW,
        "LOW": Colors.CYAN
    }

    for i, (title, desc, priority) in enumerate(insights, 1):
        print(f"  {color(f'{i}.', Colors.DIM)} {color(title, Colors.BOLD)}")
        print(f"     {desc}")
        print(f"     {color(f'[{priority}]', priority_colors[priority])}")
        print()


def display_all():
    """Display all analytics."""
    display_top_models()
    display_cost_summary()
    display_savings_analysis()
    display_token_breakdown()
    display_provider_stats()
    display_model_comparison()
    display_json_toon_analysis()
    display_ai_insights()


def main():
    """Main menu."""
    print(color("\n╔" + "═"*68 + "╗", Colors.CYAN))
    print(color("║" + " "*20 + "USAGE ANALYTICS VIEWER" + " "*26 + "║", Colors.CYAN))
    print(color("╚" + "═"*68 + "╝", Colors.CYAN))

    if not usage_tracker.enabled:
        print(color("\n⚠️  Usage tracking is DISABLED", Colors.BRIGHT_YELLOW))
        print(color("   Enable it by setting TRACK_USAGE=true in .env", Colors.YELLOW))
        print(color("   Then restart the proxy to start collecting data.\n", Colors.DIM))
        return

    print(color("\n✓ Usage tracking is ENABLED", Colors.BRIGHT_GREEN))

    while True:
        print("\n" + color("═"*70, Colors.DIM))
        print(color("  Analytics Options:", Colors.BOLD))
        print(f"    {color('1', Colors.CYAN)} - Top Models & Cost Summary")
        print(f"    {color('2', Colors.CYAN)} - Smart Routing Savings")
        print(f"    {color('3', Colors.CYAN)} - Token Composition")
        print(f"    {color('4', Colors.CYAN)} - Provider Performance")
        print(f"    {color('5', Colors.CYAN)} - Model Comparison")
        print(f"    {color('6', Colors.CYAN)} - JSON/TOON Analysis")
        print(f"    {color('7', Colors.CYAN)} - AI Insights & Recommendations")
        print(f"    {color('8', Colors.CYAN)} - Export to CSV")
        print(f"    {color('9', Colors.CYAN)} - View ALL Analytics")
        print(f"    {color('0', Colors.RED)} - Exit")
        print(color("═"*70, Colors.DIM))

        choice = input(color("\n> ", Colors.BRIGHT_GREEN)).strip()

        if choice == '1':
            display_top_models()
            display_cost_summary()
        elif choice == '2':
            display_savings_analysis()
        elif choice == '3':
            display_token_breakdown()
        elif choice == '4':
            display_provider_stats()
        elif choice == '5':
            display_model_comparison()
        elif choice == '6':
            display_json_toon_analysis()
        elif choice == '7':
            display_ai_insights()
        elif choice == '8':
            export_to_csv()
        elif choice == '9':
            display_all()
        elif choice == '0':
            print(color("\nGoodbye!\n", Colors.BRIGHT_CYAN))
            break
        else:
            print(color("\nInvalid option. Try again.", Colors.BRIGHT_RED))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(color("\n\nExiting...\n", Colors.CYAN))
        sys.exit(0)
