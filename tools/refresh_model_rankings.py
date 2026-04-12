#!/usr/bin/env python3
"""
Refresh the free-model rankings cache used by the cascade fallback system.

Fetches live model data from OpenRouter, scores each free model on:
  - tool_use support  (required for agentic tasks)
  - context length
  - output length
  - recency (stealth-free models get a recency bonus)

Writes ranked results to data/free_model_rankings.json.
Run this periodically (e.g. every 6 hours via cron) so the cascade
always has an up-to-date list of working free models.

Usage:
  python tools/refresh_model_rankings.py            # incremental (skips if cache fresh)
  python tools/refresh_model_rankings.py --force    # always re-fetch from OpenRouter
  python tools/refresh_model_rankings.py --top 10   # print top N models after refresh
"""

import argparse
import sys
from pathlib import Path

# Ensure src/ is importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.services.models.free_model_rankings import (
    build_free_model_rankings,
    save_free_model_rankings,
    get_or_build_free_model_rankings,
    RANKINGS_PATH,
)


def main():
    parser = argparse.ArgumentParser(description="Refresh OpenRouter free model rankings cache")
    parser.add_argument("--force", action="store_true", help="Force re-fetch even if cache exists")
    parser.add_argument("--top", type=int, default=0, help="Print top N models after refresh")
    args = parser.parse_args()

    print(f"[rankings] Refreshing model rankings (force={args.force})…")
    rankings = get_or_build_free_model_rankings(force_refresh=args.force)

    tool_capable = [r for r in rankings if r.supports_tools]
    print(f"[rankings] Total free models: {len(rankings)} | Tool-capable: {len(tool_capable)}")
    print(f"[rankings] Saved to: {RANKINGS_PATH}")

    if args.top > 0:
        print(f"\nTop {args.top} tool-capable free models:")
        for i, r in enumerate(tool_capable[: args.top], 1):
            print(f"  {i:2}. {r.model_id:<60} score={r.score:.1f}  ctx={r.context_length//1000}k")


if __name__ == "__main__":
    main()
