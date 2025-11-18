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

from src.utils.usage_tracker import usage_tracker
from src.utils.json_detector import json_detector


# ANSI Colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
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
        print(color("  Options:", Colors.BOLD))
        print(f"    {color('1', Colors.CYAN)} - View top models")
        print(f"    {color('2', Colors.CYAN)} - View cost summary (7 days)")
        print(f"    {color('3', Colors.CYAN)} - View JSON/TOON analysis")
        print(f"    {color('4', Colors.CYAN)} - Export to CSV")
        print(f"    {color('5', Colors.CYAN)} - View all (1-3)")
        print(f"    {color('0', Colors.RED)} - Exit")
        print(color("═"*70, Colors.DIM))

        choice = input(color("\n> ", Colors.BRIGHT_GREEN)).strip()

        if choice == '1':
            display_top_models()
        elif choice == '2':
            display_cost_summary()
        elif choice == '3':
            display_json_toon_analysis()
        elif choice == '4':
            export_to_csv()
        elif choice == '5':
            display_top_models()
            display_cost_summary()
            display_json_toon_analysis()
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
