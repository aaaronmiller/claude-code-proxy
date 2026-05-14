#!/usr/bin/env python3
"""
Failure Rate Report for Claude Code Proxy
Queries usage_tracking.db and generates failure rate statistics by model/provider/time.
"""
import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = os.path.expanduser("~/code/claude-code-proxy/usage_tracking.db")

def get_failure_stats(days=7):
    """Get failure rates by model, provider, and day."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get data for last N days
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    query = """
    SELECT 
        DATE(timestamp) as day,
        resolved_model,
        provider,
        COUNT(*) as total,
        SUM(CASE WHEN status != 'success' OR error_message != '' THEN 1 ELSE 0 END) as failures,
        AVG(CASE WHEN duration_ms > 0 THEN duration_ms ELSE NULL END) as avg_duration_ms
    FROM api_requests
    WHERE timestamp > ?
    GROUP BY day, resolved_model, provider
    ORDER BY day DESC, failures DESC
    """
    
    cursor.execute(query, (since,))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No data found in last {days} days.")
        print("NOTE: usage_tracker.log_request calls were just added to endpoints.py.")
        print("      Restart the proxy and make requests to populate the database.")
        conn.close()
        return
    
    # Process and display
    print(f"\n{'='*80}")
    print(f"FAILURE RATE REPORT (Last {days} days)")
    print(f"{'='*80}\n")
    
    # Summary by model
    print("BY MODEL:")
    print(f"{'Model':<40} {'Total':>8} {'Failures':>10} {'Failure %':>12} {'Avg Duration':>15}")
    print("-"*80)
    
    model_stats = defaultdict(lambda: {'total': 0, 'failures': 0, 'durations': []})
    for day, model, provider, total, failures, avg_dur in rows:
        if model:
            model_stats[model]['total'] += total
            model_stats[model]['failures'] += failures
            if avg_dur:
                model_stats[model]['durations'].append(avg_dur)
    
    for model in sorted(model_stats.keys(), key=lambda x: -model_stats[x]['failures']):
        stats = model_stats[model]
        failure_pct = (stats['failures'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_dur = sum(stats['durations']) / len(stats['durations']) if stats['durations'] else 0
        print(f"{model:<40} {stats['total']:>8} {stats['failures']:>10} {failure_pct:>11.1f}% {avg_dur:>14.0f}ms")
    
    # Summary by provider
    print("\n\nBY PROVIDER:")
    print(f"{'Provider':<20} {'Total':>8} {'Failures':>10} {'Failure %':>12}")
    print("-"*50)
    
    provider_stats = defaultdict(lambda: {'total': 0, 'failures': 0})
    for day, model, provider, total, failures, avg_dur in rows:
        if provider:
            provider_stats[provider]['total'] += total
            provider_stats[provider]['failures'] += failures
    
    for provider in sorted(provider_stats.keys(), key=lambda x: -provider_stats[x]['failures']):
        stats = provider_stats[provider]
        failure_pct = (stats['failures'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{provider:<20} {stats['total']:>8} {stats['failures']:>10} {failure_pct:>11.1f}%")
    
    # Daily trend
    print("\n\nDAILY TREND (Top failing models per day):")
    print(f"{'Day':<12} {'Model':<40} {'Total':>8} {'Failures':>10} {'Failure %':>12}")
    print("-"*80)
    
    current_day = None
    for day, model, provider, total, failures, avg_dur in rows:
        if day != current_day:
            if current_day is not None:
                print()
            current_day = day
        failure_pct = (failures / total * 100) if total > 0 else 0
        print(f"{day:<12} {model or 'unknown':<40} {total:>8} {failures:>10} {failure_pct:>11.1f}%")
    
    conn.close()
    
    # Recent errors
    print("\n\nRECENT ERRORS (last 10):")
    print(f"{'Timestamp':<25} {'Model':<35} {'Error'}")
    print("-"*100)
    
    cursor.execute("""
        SELECT timestamp, resolved_model, error_message
        FROM api_requests
        WHERE (status != 'success' OR error_message != '') AND timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (since,))
    
    for ts, model, error in cursor.fetchall():
        error_short = (error[:60] + '...') if error and len(error) > 60 else error
        print(f"{ts:<25} {model or 'unknown':<35} {error_short}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    get_failure_stats(days)
