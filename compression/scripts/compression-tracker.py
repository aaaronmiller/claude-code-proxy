#!/usr/bin/env python3
"""
Compression Stats Tracker - Auto-logs requests from Headroom and RTK
Integrates with compression-dashboard.py for real-time visualization
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import re

# Import dashboard for logging
sys.path.insert(0, str(Path(__file__).parent))
from compression_dashboard import CompressionDashboard

class CompressionStatsTracker:
    """Automatically tracks compression stats from Headroom and RTK logs."""
    
    def __init__(self):
        self.dashboard = CompressionDashboard()
        self.headroom_log = Path.home() / ".local/share/headroom/headroom-default.out"
        self.rtk_log = Path.home() / ".rtk/rtk.log" if os.environ.get("RTK_LOG") else None
        self.last_position = {"headroom": 0, "rtk": 0}
        
    def parse_headroom_log(self):
        """Parse Headroom logs for compression stats."""
        if not self.headroom_log.exists():
            return []
        
        events = []
        with open(self.headroom_log, 'r') as f:
            # Seek to last position
            f.seek(self.last_position["headroom"])
            
            for line in f:
                # Parse compression events
                # Format: Transform content_router: 1005 -> 1005 tokens (saved 0) [1.0ms]
                match = re.search(r'Transform content_router: (\d+) -> (\d+) tokens \(saved (\d+)\) \[(\d+\.\d+)ms\]', line)
                if match:
                    tokens_before = int(match.group(1))
                    tokens_after = int(match.group(2))
                    tokens_saved = int(match.group(3))
                    latency_ms = float(match.group(4))
                    
                    events.append({
                        "source": "headroom",
                        "tokens_in": tokens_before,
                        "tokens_out": tokens_after,
                        "tokens_saved": tokens_saved,
                        "latency_ms": latency_ms,
                        "timestamp": datetime.now().isoformat(),
                    })
            
            # Update position
            self.last_position["headroom"] = f.tell()
        
        return events
    
    def parse_rtk_log(self):
        """Parse RTK logs for compression stats."""
        if not self.rtk_log or not self.rtk_log.exists():
            return []
        
        events = []
        with open(self.rtk_log, 'r') as f:
            f.seek(self.last_position["rtk"])
            
            for line in f:
                # RTK log format varies - look for compression stats
                if "compressed" in line.lower() or "saved" in line.lower():
                    # Try to extract numbers
                    match = re.search(r'(\d+)\s*tokens?.*saved|saved.*?(\d+)\s*tokens', line, re.IGNORECASE)
                    if match:
                        tokens_saved = int(match.group(1) or match.group(2))
                        
                        events.append({
                            "source": "rtk",
                            "tokens_saved": tokens_saved,
                            "latency_ms": 5,  # RTK average overhead
                            "timestamp": datetime.now().isoformat(),
                        })
            
            self.last_position["rtk"] = f.tell()
        
        return events
    
    def log_events(self, events):
        """Log parsed events to dashboard."""
        for event in events:
            self.dashboard.log_request(
                tokens_in=event.get("tokens_in", 0),
                tokens_out=event.get("tokens_out", 0),
                tokens_saved=event.get("tokens_saved", 0),
                model="qwen/qwen3.5-9b",  # Default model
                latency_ms=event.get("latency_ms", 0),
                headroom_latency_ms=event.get("latency_ms", 0) if event["source"] == "headroom" else 0,
                rtk_latency_ms=event.get("latency_ms", 0) if event["source"] == "rtk" else 0,
            )
    
    def run(self, interval=2):
        """Run the tracker."""
        print("🔍 Starting Compression Stats Tracker...")
        print(f"   Headroom log: {self.headroom_log}")
        print(f"   RTK log: {self.rtk_log or 'Not configured'}")
        print(f"   Polling interval: {interval}s")
        print()
        
        try:
            while True:
                # Parse logs
                headroom_events = self.parse_headroom_log()
                rtk_events = self.parse_rtk_log()
                
                # Log events
                if headroom_events or rtk_events:
                    all_events = headroom_events + rtk_events
                    self.log_events(all_events)
                    print(f"✓ Logged {len(all_events)} events ({len(headroom_events)} headroom, {len(rtk_events)} rtk)")
                
                # Save stats
                self.dashboard.save_stats()
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Saving stats and exiting...")
            self.dashboard.save_stats()
            print("✓ Stats saved")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Compression Stats Tracker")
    parser.add_argument("--interval", type=int, default=2, help="Polling interval in seconds")
    args = parser.parse_args()
    
    tracker = CompressionStatsTracker()
    tracker.run(interval=args.interval)


if __name__ == "__main__":
    main()
