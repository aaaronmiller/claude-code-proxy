#!/usr/bin/env python3
"""
Automatic log cleanup for Claude Code Proxy.

Removes log files older than retention period and enforces size limits.
Before cleanup, aggregates analytics data into compact summary format.

Usage:
    python -m src.services.logging.log_cleanup
    # Or with custom settings:
    LOG_RETENTION_DAYS=3 LOG_MAX_SIZE_MB=200 python -m src.services.logging.log_cleanup

Cron example (daily at 3 AM):
    0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict, Any, List
from collections import defaultdict


def aggregate_analytics_data(logs_dir: Path) -> Dict[str, Any]:
    """
    Aggregate analytics data from JSONL files before cleanup.
    
    Reads tool_analytics.jsonl and cache_analytics.jsonl,
    computes summary statistics, and returns compact metadata.
    
    Returns a dictionary with:
    - timestamp: When aggregation was performed
    - period_start: Start of aggregation period
    - period_end: End of aggregation period
    - tool_calls: Aggregated tool call statistics
    - cache_usage: Aggregated cache statistics
    - sessions: Unique session count
    - summary: One-line human-readable summary
    """
    summary = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'period_start': None,
        'period_end': None,
        'tool_calls': {
            'total': 0,
            'success': 0,
            'failure': 0,
            'by_tool': defaultdict(lambda: {'success': 0, 'failure': 0}),
            'success_rate': 0
        },
        'cache_usage': {
            'total_requests': 0,
            'hits': 0,
            'misses': 0,
            'cached_tokens': 0,
            'total_tokens': 0,
            'hit_rate': 0,
            'token_savings_percent': 0
        },
        'sessions': set(),
        'summary': ''
    }
    
    # Aggregate tool analytics
    tool_file = logs_dir / 'tool_analytics.jsonl'
    if tool_file.exists():
        try:
            with open(tool_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        timestamp = data.get('timestamp', '')
                        
                        # Track period
                        if summary['period_start'] is None or timestamp < summary['period_start']:
                            summary['period_start'] = timestamp
                        if summary['period_end'] is None or timestamp > summary['period_end']:
                            summary['period_end'] = timestamp
                        
                        # Aggregate tool stats
                        summary['tool_calls']['total'] += 1
                        if data.get('success', True):
                            summary['tool_calls']['success'] += 1
                            summary['tool_calls']['by_tool'][data.get('tool_name', 'unknown')]['success'] += 1
                        else:
                            summary['tool_calls']['failure'] += 1
                            summary['tool_calls']['by_tool'][data.get('tool_name', 'unknown')]['failure'] += 1
                        
                        # Track sessions
                        if data.get('session_id'):
                            summary['sessions'].add(data['session_id'])
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            print(f"   ⚠️  Error reading tool analytics: {e}")
    
    # Calculate tool success rate
    if summary['tool_calls']['total'] > 0:
        summary['tool_calls']['success_rate'] = round(
            summary['tool_calls']['success'] / summary['tool_calls']['total'] * 100, 1
        )
    
    # Aggregate cache analytics
    cache_file = logs_dir / 'cache_analytics.jsonl'
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        timestamp = data.get('timestamp', '')
                        
                        # Track period
                        if summary['period_start'] is None or timestamp < summary['period_start']:
                            summary['period_start'] = timestamp
                        if summary['period_end'] is None or timestamp > summary['period_end']:
                            summary['period_end'] = timestamp
                        
                        # Aggregate cache stats
                        summary['cache_usage']['total_requests'] += 1
                        if data.get('cache_hit', False):
                            summary['cache_usage']['hits'] += 1
                            summary['cache_usage']['cached_tokens'] += data.get('cached_tokens', 0)
                        else:
                            summary['cache_usage']['misses'] += 1
                        
                        summary['cache_usage']['total_tokens'] += data.get('total_tokens', 0)
                        
                        # Track sessions
                        if data.get('session_id'):
                            summary['sessions'].add(data['session_id'])
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            print(f"   ⚠️  Error reading cache analytics: {e}")
    
    # Calculate cache rates
    if summary['cache_usage']['total_requests'] > 0:
        summary['cache_usage']['hit_rate'] = round(
            summary['cache_usage']['hits'] / summary['cache_usage']['total_requests'] * 100, 1
        )
    if summary['cache_usage']['total_tokens'] > 0:
        summary['cache_usage']['token_savings_percent'] = round(
            summary['cache_usage']['cached_tokens'] / summary['cache_usage']['total_tokens'] * 100, 1
        )
    
    # Convert sessions set to count
    session_count = len(summary['sessions'])
    summary['sessions'] = session_count
    
    # Convert defaultdict to regular dict for JSON serialization
    summary['tool_calls']['by_tool'] = dict(summary['tool_calls']['by_tool'])
    
    # Generate one-line summary
    summary['summary'] = (
        f"Period: {summary['period_start'] or 'N/A'} to {summary['period_end'] or 'N/A'} | "
        f"Tools: {summary['tool_calls']['total']} calls ({summary['tool_calls']['success_rate']}% success) | "
        f"Cache: {summary['cache_usage']['hit_rate']}% hit rate ({summary['cache_usage']['cached_tokens']:,} tokens) | "
        f"Sessions: {session_count}"
    )
    
    return summary


def save_aggregated_summary(logs_dir: Path, summary: Dict[str, Any], dry_run: bool = False) -> bool:
    """
    Save aggregated summary to metrics_history.jsonl.
    
    This file contains one line per cleanup cycle with compact statistics.
    Raw analytics files can then be safely deleted.
    
    Args:
        logs_dir: Directory containing log files
        summary: Aggregated summary dictionary
        dry_run: If True, don't actually write
    
    Returns:
        True if successful, False otherwise
    """
    history_file = logs_dir / 'metrics_history.jsonl'
    
    if dry_run:
        print(f"   Would save summary to: {history_file}")
        print(f"   Summary: {summary['summary']}")
        return True
    
    try:
        with open(history_file, 'a') as f:
            f.write(json.dumps(summary) + '\n')
        print(f"   ✅ Saved aggregated metrics to: {history_file.name}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to save summary: {e}")
        return False


def get_file_age_days(file_path: Path) -> int:
    """Get file age in days based on modification time."""
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return (datetime.now() - mtime).days


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB."""
    return file_path.stat().st_size / (1024 * 1024)


def cleanup_logs(
    logs_dir: str = None,
    retention_days: int = None,
    max_size_mb: int = None,
    dry_run: bool = False,
    aggregate_before_cleanup: bool = True
) -> Tuple[int, float]:
    """
    Clean up old log files and enforce size limits.
    
    Before cleanup, aggregates analytics data into compact summary format.
    
    Args:
        logs_dir: Directory containing log files. Defaults to 'logs/' in project root.
        retention_days: Remove files older than this. Defaults to LOG_RETENTION_DAYS or 7.
        max_size_mb: Maximum total log size in MB. Defaults to LOG_MAX_SIZE_MB or 500.
        dry_run: If True, only report what would be removed.
        aggregate_before_cleanup: If True, aggregate analytics before deleting (default: True).
    
    Returns:
        Tuple of (files_removed, total_size_freed_mb)
    """
    # Configuration with defaults
    logs_dir = Path(logs_dir or os.getenv("LOGS_DIR", "logs"))
    retention_days = int(retention_days or os.getenv("LOG_RETENTION_DAYS", "7"))
    max_size_mb = int(max_size_mb or os.getenv("LOG_MAX_SIZE_MB", "500"))
    
    # Ensure logs directory exists
    if not logs_dir.exists():
        print(f"ℹ️  Logs directory does not exist: {logs_dir}")
        return 0, 0.0
    
    print(f"🧹 Starting log cleanup")
    print(f"   Directory: {logs_dir.absolute()}")
    print(f"   Retention: {retention_days} days")
    print(f"   Max size: {max_size_mb} MB")
    print()
    
    # Step 1: Aggregate analytics before cleanup
    if aggregate_before_cleanup:
        print(f"📊 Step 1: Aggregating analytics data...")
        analytics_files = ['tool_analytics.jsonl', 'cache_analytics.jsonl']
        has_analytics = any((logs_dir / f).exists() for f in analytics_files)
        
        if has_analytics:
            summary = aggregate_analytics_data(logs_dir)
            
            if summary['period_start']:  # Has data
                save_aggregated_summary(logs_dir, summary, dry_run)
            else:
                print(f"   ℹ️  No analytics data to aggregate")
        else:
            print(f"   ℹ️  No analytics files found")
        
        print()
    
    # Get all log files
    log_files = list(logs_dir.glob("*.log")) + list(logs_dir.glob("*.jsonl"))
    # Exclude metrics_history.jsonl from cleanup
    log_files = [f for f in log_files if f.name != 'metrics_history.jsonl']
    
    if not log_files:
        print("✅ No log files to clean up")
        return 0, 0.0
    
    # Calculate current total size
    total_size_mb = sum(get_file_size_mb(f) for f in log_files)
    
    print(f"📊 Current state:")
    print(f"   Files: {len(log_files)}")
    print(f"   Total size: {total_size_mb:.1f} MB")
    print()
    
    # Phase 1: Remove old files
    print(f"📅 Phase 1: Removing files older than {retention_days} days...")
    removed_count = 0
    freed_mb = 0.0
    
    for log_file in sorted(log_files):  # Sort for consistent output
        age_days = get_file_age_days(log_file)
        
        if age_days > retention_days:
            size_mb = get_file_size_mb(log_file)
            action = "Would remove" if dry_run else "Removing"
            print(f"   {action}: {log_file.name} (age: {age_days}d, size: {size_mb:.1f}MB)")
            
            if not dry_run:
                log_file.unlink()
            
            removed_count += 1
            freed_mb += size_mb
    
    if removed_count == 0:
        print(f"   ✅ No files exceeded retention period")
    else:
        action = "Would remove" if dry_run else "Removed"
        print(f"   ✅ {action} {removed_count} files ({freed_mb:.1f} MB)")
    
    print()
    
    # Refresh file list if we removed files
    if removed_count > 0 and not dry_run:
        log_files = list(logs_dir.glob("*.log")) + list(logs_dir.glob("*.jsonl"))
        log_files = [f for f in log_files if f.name != 'metrics_history.jsonl']
        total_size_mb = sum(get_file_size_mb(f) for f in log_files)
    
    # Phase 2: Enforce size limit
    print(f"💾 Phase 2: Enforcing {max_size_mb} MB size limit...")
    
    if total_size_mb <= max_size_mb:
        print(f"   ✅ Total size ({total_size_mb:.1f} MB) is within limit")
    else:
        print(f"   ⚠️  Total size ({total_size_mb:.1f} MB) exceeds limit")
        print(f"   Removing oldest files until under {max_size_mb} MB...")
        
        # Sort by modification time (oldest first)
        log_files_sorted = sorted(log_files, key=lambda f: f.stat().st_mtime)
        
        size_freed = 0.0
        for log_file in log_files_sorted:
            if total_size_mb - size_freed <= max_size_mb:
                break
            
            size_mb = get_file_size_mb(log_file)
            age_days = get_file_age_days(log_file)
            action = "Would remove" if dry_run else "Removing"
            print(f"   {action}: {log_file.name} (age: {age_days}d, size: {size_mb:.1f}MB)")
            
            if not dry_run:
                log_file.unlink()
            
            removed_count += 1
            size_freed += size_mb
        
        print(f"   ✅ Freed {size_freed:.1f} MB")
        freed_mb += size_freed
    
    print()
    
    # Final state
    if not dry_run:
        log_files = list(logs_dir.glob("*.log")) + list(logs_dir.glob("*.jsonl"))
        log_files = [f for f in log_files if f.name != 'metrics_history.jsonl']
        total_size_mb = sum(get_file_size_mb(f) for f in log_files)
    
    print(f"📊 Final state:")
    print(f"   Files: {len(log_files)}")
    print(f"   Total size: {total_size_mb:.1f} MB")
    
    # Show metrics history if it exists
    history_file = logs_dir / 'metrics_history.jsonl'
    if history_file.exists():
        history_size = get_file_size_mb(history_file)
        history_lines = sum(1 for _ in open(history_file))
        print(f"   Metrics history: {history_lines} snapshots ({history_size:.2f} MB)")
    
    print()
    
    # Summary
    if dry_run:
        print(f"🔍 DRY RUN - No files actually removed")
        print(f"   Would remove {removed_count} files")
        print(f"   Would free {freed_mb:.1f} MB")
    else:
        print(f"✅ Cleanup complete")
        print(f"   Removed {removed_count} files")
        print(f"   Freed {freed_mb:.1f} MB")
    
    return removed_count, freed_mb


def cleanup_old_forensic_logs(logs_dir: str = None, max_age_days: int = 3):
    """
    Clean up forensic log files older than specified days.
    
    Forensic logs are named like: forensic_YYYYMMDD_HHMMSS.log
    
    Args:
        logs_dir: Directory containing log files
        max_age_days: Remove forensic logs older than this
    """
    logs_dir = Path(logs_dir or os.getenv("LOGS_DIR", "logs"))
    
    if not logs_dir.exists():
        return 0
    
    print(f"🧹 Cleaning up forensic logs older than {max_age_days} days...")
    
    removed = 0
    for log_file in logs_dir.glob("forensic_*.log"):
        age_days = get_file_age_days(log_file)
        if age_days > max_age_days:
            size_mb = get_file_size_mb(log_file)
            print(f"   Removing: {log_file.name} (age: {age_days}d, size: {size_mb:.1f}MB)")
            log_file.unlink()
            removed += 1
    
    if removed == 0:
        print(f"   ✅ No old forensic logs found")
    else:
        print(f"   ✅ Removed {removed} forensic log(s)")
    
    return removed


def view_metrics_history(logs_dir: str = None, limit: int = 10):
    """
    View recent entries from metrics history.
    
    Args:
        logs_dir: Directory containing log files
        limit: Number of entries to show
    """
    logs_dir = Path(logs_dir or os.getenv("LOGS_DIR", "logs"))
    history_file = logs_dir / 'metrics_history.jsonl'
    
    if not history_file.exists():
        print("ℹ️  No metrics history available yet")
        return
    
    print(f"📊 Recent Metrics History (last {limit} entries):")
    print("=" * 80)
    
    try:
        with open(history_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines[-limit:]:
            data = json.loads(line.strip())
            print(f"\n📅 {data.get('timestamp', 'Unknown')[:10]}")
            print(f"   Period: {data.get('period_start', 'N/A')[:10]} to {data.get('period_end', 'N/A')[:10]}")
            print(f"   {data.get('summary', 'No summary')}")
            
            # Show key stats
            tool_calls = data.get('tool_calls', {})
            cache = data.get('cache_usage', {})
            print(f"   Tools: {tool_calls.get('total', 0)} calls, {tool_calls.get('success_rate', 0)}% success")
            print(f"   Cache: {cache.get('hit_rate', 0)}% hit rate, {cache.get('cached_tokens', 0):,} tokens saved")
            print(f"   Sessions: {data.get('sessions', 0)} unique")
    
    except Exception as e:
        print(f"❌ Error reading history: {e}")


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up old log files and enforce size limits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run cleanup with default settings
  python -m src.services.logging.log_cleanup
  
  # Dry run (see what would be removed)
  python -m src.services.logging.log_cleanup --dry-run
  
  # Custom retention (3 days)
  LOG_RETENTION_DAYS=3 python -m src.services.logging.log_cleanup
  
  # Custom size limit (200 MB)
  LOG_MAX_SIZE_MB=200 python -m src.services.logging.log_cleanup
  
  # Custom logs directory
  LOGS_DIR=/var/log/claude-proxy python -m src.services.logging.log_cleanup
  
  # View metrics history
  python -m src.services.logging.log_cleanup --view-history

Cron setup (daily at 3 AM):
  0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing"
    )
    
    parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help="Override retention period (days)"
    )
    
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=None,
        help="Override maximum total size (MB)"
    )
    
    parser.add_argument(
        "--logs-dir",
        type=str,
        default=None,
        help="Override logs directory path"
    )
    
    parser.add_argument(
        "--clean-forensic",
        action="store_true",
        help="Also clean up old forensic logs"
    )
    
    parser.add_argument(
        "--no-aggregate",
        action="store_true",
        help="Skip aggregation step (faster, but loses analytics data)"
    )
    
    parser.add_argument(
        "--view-history",
        action="store_true",
        help="View recent metrics history instead of cleaning"
    )
    
    parser.add_argument(
        "--history-limit",
        type=int,
        default=10,
        help="Number of history entries to show (default: 10)"
    )
    
    args = parser.parse_args()
    
    # View history mode
    if args.view_history:
        view_metrics_history(logs_dir=args.logs_dir, limit=args.history_limit)
        sys.exit(0)
    
    # Run main cleanup
    removed, freed = cleanup_logs(
        logs_dir=args.logs_dir,
        retention_days=args.retention_days,
        max_size_mb=args.max_size_mb,
        dry_run=args.dry_run,
        aggregate_before_cleanup=not args.no_aggregate
    )
    
    # Optionally clean forensic logs
    if args.clean_forensic:
        print()
        cleanup_old_forensic_logs(logs_dir=args.logs_dir)
    
    # Exit with appropriate code
    sys.exit(0)


if __name__ == "__main__":
    main()
