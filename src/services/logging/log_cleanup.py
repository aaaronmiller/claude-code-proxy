#!/usr/bin/env python3
"""
Automatic log cleanup for Claude Code Proxy.

Removes log files older than retention period and enforces size limits.
Designed to run daily via cron or as a systemd timer.

Usage:
    python -m src.services.logging.log_cleanup
    # Or with custom settings:
    LOG_RETENTION_DAYS=3 LOG_MAX_SIZE_MB=200 python -m src.services.logging.log_cleanup

Cron example (daily at 3 AM):
    0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple


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
    dry_run: bool = False
) -> Tuple[int, float]:
    """
    Clean up old log files and enforce size limits.
    
    Args:
        logs_dir: Directory containing log files. Defaults to 'logs/' in project root.
        retention_days: Remove files older than this. Defaults to LOG_RETENTION_DAYS or 7.
        max_size_mb: Maximum total log size in MB. Defaults to LOG_MAX_SIZE_MB or 500.
        dry_run: If True, only report what would be removed.
    
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
    
    # Get all log files
    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        print("✅ No log files found")
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
        log_files = list(logs_dir.glob("*.log"))
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
        log_files = list(logs_dir.glob("*.log"))
        total_size_mb = sum(get_file_size_mb(f) for f in log_files)
    
    print(f"📊 Final state:")
    print(f"   Files: {len(log_files)}")
    print(f"   Total size: {total_size_mb:.1f} MB")
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
    
    Forensic logs are named like: forensic_20260316_143022.log
    
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

Cron setup (daily at 3 AM):
  0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup >> /var/log/claude-cleanup.log 2>&1
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
    
    args = parser.parse_args()
    
    # Run main cleanup
    removed, freed = cleanup_logs(
        logs_dir=args.logs_dir,
        retention_days=args.retention_days,
        max_size_mb=args.max_size_mb,
        dry_run=args.dry_run
    )
    
    # Optionally clean forensic logs
    if args.clean_forensic:
        print()
        cleanup_old_forensic_logs(logs_dir=args.logs_dir)
    
    # Exit with appropriate code
    if removed > 0:
        sys.exit(0)  # Success, files removed
    else:
        sys.exit(0)  # Success, nothing to remove


if __name__ == "__main__":
    main()
