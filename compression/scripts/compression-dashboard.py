#!/usr/bin/env python3
"""
Compression Stack Dashboard - Real-time Visualization
Shows token savings, cost savings, latency, and resource usage
Usage: python3 compression-dashboard.py [--web]
"""

import json
import time
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import subprocess
import threading

# Try to import plotly for graphs, fall back to ASCII if not available
try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("⚠ Plotly not installed - using ASCII charts")
    print("  Install: pip install plotly")

# OpenRouter pricing (per 1M tokens) - Updated 2026
OPENROUTER_PRICING = {
    # Premium models
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    
    # Mid-tier models
    "qwen/qwen3.5-9b": {"input": 0.05, "output": 0.10},
    "qwen/qwen3.5-72b": {"input": 0.30, "output": 0.50},
    "qwen/qwen3.6-plus-preview:free": {"input": 0.0, "output": 0.0},  # Free tier
    
    # Budget models
    "minimax/minimax-m2.5:free": {"input": 0.0, "output": 0.0},
    "nvidia/nemotron-3-super-120b-a12b": {"input": 0.0, "output": 0.0},
    
    # Default (if model not found)
    "default": {"input": 0.50, "output": 1.50},
}

# RTK compression stats (from research)
RTK_COMPRESSION_STATS = {
    "avg_compression_rate": 0.889,  # 88.9% average savings
    "commands_processed": 15720,
    "tokens_saved_total": 138000000,
    "latency_overhead_ms": 5,  # ~5ms average overhead
}

# Headroom compression stats (from our testing)
HEADROOM_COMPRESSION_STATS = {
    "avg_compression_rate": 0.97,  # 97% savings
    "latency_overhead_ms": 50,  # ~50ms for model inference
    "gpu_vram_mb": 5311,  # Current VRAM usage
}


class CompressionDashboard:
    """Real-time compression and cost tracking dashboard."""
    
    def __init__(self):
        self.data_file = Path.home() / ".compression_stats.json"
        self.stats = self.load_stats()
        self.start_time = time.time()
        
    def load_stats(self):
        """Load persistent stats from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Initialize fresh stats
        return {
            "sessions": [],
            "hourly": defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0, "tokens_saved": 0, "cost_without": 0, "cost_with": 0}),
            "daily": defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0, "tokens_saved": 0, "cost_without": 0, "cost_with": 0}),
            "total": {"tokens_in": 0, "tokens_out": 0, "tokens_saved": 0, "cost_without": 0, "cost_with": 0, "requests": 0},
            "latency": {"headroom_ms": [], "rtk_ms": [], "total_ms": []},
        }
    
    def save_stats(self):
        """Save stats to file."""
        # Convert defaultdicts to regular dicts for JSON serialization
        save_data = {
            "sessions": self.stats["sessions"][-1000:],  # Keep last 1000 sessions
            "hourly": dict(self.stats["hourly"]),
            "daily": dict(self.stats["daily"]),
            "total": self.stats["total"],
            "latency": {
                "headroom_ms": self.stats["latency"]["headroom_ms"][-100:],
                "rtk_ms": self.stats["latency"]["rtk_ms"][-100:],
                "total_ms": self.stats["latency"]["total_ms"][-100:],
            }
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(save_data, f, indent=2)
    
    def log_request(self, tokens_in: int, tokens_out: int, tokens_saved: int, 
                    model: str = "default", latency_ms: float = 0, headroom_latency_ms: float = 0, rtk_latency_ms: float = 0):
        """Log a compression request."""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d %H:00")
        day_key = now.strftime("%Y-%m-%d")
        
        # Calculate costs
        pricing = OPENROUTER_PRICING.get(model, OPENROUTER_PRICING["default"])
        cost_without = (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000
        cost_with = ((tokens_in - tokens_saved) * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000
        
        # Update totals
        self.stats["total"]["tokens_in"] += tokens_in
        self.stats["total"]["tokens_out"] += tokens_out
        self.stats["total"]["tokens_saved"] += tokens_saved
        self.stats["total"]["cost_without"] += cost_without
        self.stats["total"]["cost_with"] += cost_with
        self.stats["total"]["requests"] += 1
        
        # Update hourly
        self.stats["hourly"][hour_key]["tokens_in"] += tokens_in
        self.stats["hourly"][hour_key]["tokens_out"] += tokens_out
        self.stats["hourly"][hour_key]["tokens_saved"] += tokens_saved
        self.stats["hourly"][hour_key]["cost_without"] += cost_without
        self.stats["hourly"][hour_key]["cost_with"] += cost_with
        
        # Update daily
        self.stats["daily"][day_key]["tokens_in"] += tokens_in
        self.stats["daily"][day_key]["tokens_out"] += tokens_out
        self.stats["daily"][day_key]["tokens_saved"] += tokens_saved
        self.stats["daily"][day_key]["cost_without"] += cost_without
        self.stats["daily"][day_key]["cost_with"] += cost_with
        
        # Log session
        self.stats["sessions"].append({
            "timestamp": now.isoformat(),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_saved": tokens_saved,
            "model": model,
            "latency_ms": latency_ms,
            "headroom_latency_ms": headroom_latency_ms,
            "rtk_latency_ms": rtk_latency_ms,
            "cost_saved": cost_without - cost_with,
        })
        
        # Log latency
        self.stats["latency"]["headroom_ms"].append(headroom_latency_ms)
        self.stats["latency"]["rtk_ms"].append(rtk_latency_ms)
        self.stats["latency"]["total_ms"].append(latency_ms)
        
        # Keep latency lists manageable
        for key in self.stats["latency"]:
            if len(self.stats["latency"][key]) > 100:
                self.stats["latency"][key] = self.stats["latency"][key][-100:]
        
        # Save periodically
        if self.stats["total"]["requests"] % 10 == 0:
            self.save_stats()
    
    def get_summary(self):
        """Get summary statistics."""
        total = self.stats["total"]
        savings_pct = (total["tokens_saved"] / total["tokens_in"] * 100) if total["tokens_in"] > 0 else 0
        cost_savings = total["cost_without"] - total["cost_with"]
        cost_savings_pct = (cost_savings / total["cost_without"] * 100) if total["cost_without"] > 0 else 0
        
        # Latency averages
        avg_headroom = sum(self.stats["latency"]["headroom_ms"]) / len(self.stats["latency"]["headroom_ms"]) if self.stats["latency"]["headroom_ms"] else 0
        avg_rtk = sum(self.stats["latency"]["rtk_ms"]) / len(self.stats["latency"]["rtk_ms"]) if self.stats["latency"]["rtk_ms"] else 0
        avg_total = sum(self.stats["latency"]["total_ms"]) / len(self.stats["latency"]["total_ms"]) if self.stats["latency"]["total_ms"] else 0
        
        return {
            "requests": total["requests"],
            "tokens_in": total["tokens_in"],
            "tokens_out": total["tokens_out"],
            "tokens_saved": total["tokens_saved"],
            "savings_pct": savings_pct,
            "cost_without": total["cost_without"],
            "cost_with": total["cost_with"],
            "cost_savings": cost_savings,
            "cost_savings_pct": cost_savings_pct,
            "avg_headroom_latency_ms": avg_headroom,
            "avg_rtk_latency_ms": avg_rtk,
            "avg_total_latency_ms": avg_total,
        }
    
    def render_ascii_dashboard(self):
        """Render ASCII dashboard for terminal."""
        summary = self.get_summary()
        
        # Clear screen
        os.system('clear' if os.name != 'nt' else 'cls')
        
        print("=" * 80)
        print("  COMPRESSION STACK DASHBOARD - REAL-TIME MONITORING")
        print("=" * 80)
        print()
        
        # Summary stats
        print("📊 SUMMARY")
        print("-" * 80)
        print(f"  Requests:           {summary['requests']:,}")
        print(f"  Tokens In:          {summary['tokens_in']:,}")
        print(f"  Tokens Out:         {summary['tokens_out']:,}")
        print(f"  Tokens Saved:       {summary['tokens_saved']:,} ({summary['savings_pct']:.1f}%)")
        print()
        
        # Cost savings
        print("💰 COST SAVINGS")
        print("-" * 80)
        print(f"  Cost Without Compression:  ${summary['cost_without']:.4f}")
        print(f"  Cost With Compression:     ${summary['cost_with']:.4f}")
        print(f"  Total Savings:             ${summary['cost_savings']:.4f} ({summary['cost_savings_pct']:.1f}%)")
        print()
        
        # Latency
        print("⏱️  LATENCY")
        print("-" * 80)
        print(f"  Headroom Overhead:    {summary['avg_headroom_latency_ms']:.1f} ms")
        print(f"  RTK Overhead:         {summary['avg_rtk_latency_ms']:.1f} ms")
        print(f"  Total Overhead:       {summary['avg_total_latency_ms']:.1f} ms")
        print()
        
        # Hourly breakdown
        print("📈 HOURLY BREAKDOWN (Last 24 Hours)")
        print("-" * 80)
        
        hourly_data = sorted(self.stats["hourly"].items())[-24:]
        if hourly_data:
            max_tokens = max(h[1]["tokens_saved"] for h in hourly_data) if hourly_data else 1
            
            for hour, data in hourly_data:
                bar_len = int((data["tokens_saved"] / max_tokens) * 40) if max_tokens > 0 else 0
                bar = "█" * bar_len + "░" * (40 - bar_len)
                print(f"  {hour}  {bar}  {data['tokens_saved']:,} tokens (${data['cost_without'] - data['cost_with']:.4f} saved)")
        else:
            print("  No hourly data yet")
        
        print()
        
        # Daily breakdown
        print("📅 DAILY BREAKDOWN (Last 7 Days)")
        print("-" * 80)
        
        daily_data = sorted(self.stats["daily"].items())[-7:]
        if daily_data:
            max_tokens = max(d[1]["tokens_saved"] for d in daily_data) if daily_data else 1
            
            for day, data in daily_data:
                bar_len = int((data["tokens_saved"] / max_tokens) * 40) if max_tokens > 0 else 0
                bar = "█" * bar_len + "░" * (40 - bar_len)
                print(f"  {day}  {bar}  {data['tokens_saved']:,} tokens (${data['cost_without'] - data['cost_with']:.4f} saved)")
        else:
            print("  No daily data yet")
        
        print()
        
        # GPU status
        print("🎮 GPU STATUS")
        print("-" * 80)
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            print(f"  {result.stdout.strip()}")
        except:
            print("  GPU monitoring unavailable")
        
        print()
        print("=" * 80)
        print("  Press Ctrl+C to exit | Data auto-saves every 10 requests")
        print("=" * 80)
    
    def render_web_dashboard(self):
        """Generate HTML dashboard with Plotly graphs."""
        if not HAS_PLOTLY:
            print("❌ Plotly not installed. Run: pip install plotly")
            return
        
        summary = self.get_summary()
        
        # Create figures
        fig_hourly = self._create_hourly_chart()
        fig_daily = self._create_daily_chart()
        fig_latency = self._create_latency_chart()
        fig_savings = self._create_savings_chart()
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Compression Stack Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #00d4ff; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }}
        .card {{ background: #1a1a2e; border-radius: 8px; padding: 20px; }}
        .stat {{ font-size: 24px; font-weight: bold; color: #00ff88; }}
        .stat-label {{ color: #888; font-size: 14px; }}
        .latency {{ color: #ffa502; }}
        .savings {{ color: #00d4ff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Compression Stack Dashboard</h1>
        <p>Real-time token savings, cost tracking, and latency monitoring</p>
        
        <div class="grid">
            <div class="card">
                <div class="stat-label">Total Requests</div>
                <div class="stat">{summary['requests']:,}</div>
            </div>
            <div class="card">
                <div class="stat-label">Compression Rate</div>
                <div class="stat">{summary['savings_pct']:.1f}%</div>
            </div>
            <div class="card">
                <div class="stat-label">Tokens Saved</div>
                <div class="stat savings">{summary['tokens_saved']:,}</div>
            </div>
            <div class="card">
                <div class="stat-label">Cost Savings</div>
                <div class="stat savings">${summary['cost_savings']:.4f}</div>
            </div>
            <div class="card">
                <div class="stat-label">Headroom Latency</div>
                <div class="stat latency">{summary['avg_headroom_latency_ms']:.1f} ms</div>
            </div>
            <div class="card">
                <div class="stat-label">Total Latency Overhead</div>
                <div class="stat latency">{summary['avg_total_latency_ms']:.1f} ms</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" id="hourly-chart"></div>
            <div class="card" id="daily-chart"></div>
            <div class="card" id="latency-chart"></div>
            <div class="card" id="savings-chart"></div>
        </div>
    </div>
    
    <script>
        // Hourly chart
        {self._plotly_json(fig_hourly, 'hourly-chart')}
        
        // Daily chart
        {self._plotly_json(fig_daily, 'daily-chart')}
        
        // Latency chart
        {self._plotly_json(fig_latency, 'latency-chart')}
        
        // Savings chart
        {self._plotly_json(fig_savings, 'savings-chart')}
    </script>
</body>
</html>
"""
        
        # Save HTML
        html_file = Path.home() / ".compression_dashboard.html"
        with open(html_file, 'w') as f:
            f.write(html)
        
        print(f"✓ Dashboard saved to: {html_file}")
        print(f"  Open in browser: file://{html_file}")
    
    def _create_hourly_chart(self):
        """Create hourly savings chart."""
        hourly_data = sorted(self.stats["hourly"].items())[-24:]
        if not hourly_data:
            return go.Figure().add_annotation(text="No data yet", showarrow=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[h[0].split()[-1] for h in hourly_data],
            y=[h[1]["tokens_saved"] for h in hourly_data],
            name="Tokens Saved",
            marker_color="#00d4ff"
        ))
        fig.update_layout(
            title="Hourly Token Savings (Last 24 Hours)",
            xaxis_title="Hour",
            yaxis_title="Tokens Saved",
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#1a1a2e',
            font=dict(color='#e0e0e0')
        )
        return fig
    
    def _create_daily_chart(self):
        """Create daily savings chart."""
        daily_data = sorted(self.stats["daily"].items())[-7:]
        if not daily_data:
            return go.Figure().add_annotation(text="No data yet", showarrow=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[d[0] for d in daily_data],
            y=[d[1]["tokens_saved"] for d in daily_data],
            name="Tokens Saved",
            marker_color="#00ff88"
        ))
        fig.update_layout(
            title="Daily Token Savings (Last 7 Days)",
            xaxis_title="Date",
            yaxis_title="Tokens Saved",
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#1a1a2e',
            font=dict(color='#e0e0e0')
        )
        return fig
    
    def _create_latency_chart(self):
        """Create latency distribution chart."""
        fig = go.Figure()
        
        if self.stats["latency"]["headroom_ms"]:
            fig.add_trace(go.Histogram(
                x=self.stats["latency"]["headroom_ms"],
                name="Headroom",
                marker_color="#00d4ff",
                opacity=0.7
            ))
        
        if self.stats["latency"]["rtk_ms"]:
            fig.add_trace(go.Histogram(
                x=self.stats["latency"]["rtk_ms"],
                name="RTK",
                marker_color="#ffa502",
                opacity=0.7
            ))
        
        fig.update_layout(
            title="Latency Distribution",
            xaxis_title="Latency (ms)",
            yaxis_title="Frequency",
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#1a1a2e',
            font=dict(color='#e0e0e0')
        )
        return fig
    
    def _create_savings_chart(self):
        """Create cost savings chart."""
        daily_data = sorted(self.stats["daily"].items())[-7:]
        if not daily_data:
            return go.Figure().add_annotation(text="No data yet", showarrow=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[d[0] for d in daily_data],
            y=[d[1]["cost_without"] - d[1]["cost_with"] for d in daily_data],
            name="Cost Savings ($)",
            marker_color="#00ff88"
        ))
        fig.update_layout(
            title="Daily Cost Savings (Last 7 Days)",
            xaxis_title="Date",
            yaxis_title="Savings ($)",
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#1a1a2e',
            font=dict(color='#e0e0e0')
        )
        return fig
    
    def _plotly_json(self, fig, div_id):
        """Convert Plotly figure to JSON for embedding."""
        return f"Plotly.newPlot('{div_id}', {fig.to_json()}, {{responsive: true}});"
    
    def run(self, web=False, interval=5):
        """Run the dashboard."""
        print("🚀 Starting Compression Dashboard...")
        print(f"   Mode: {'Web' if web else 'Terminal'}")
        print(f"   Update interval: {interval}s")
        print()
        
        try:
            while True:
                if web:
                    self.render_web_dashboard()
                else:
                    self.render_ascii_dashboard()
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Saving stats and exiting...")
            self.save_stats()
            print("✓ Stats saved")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Compression Stack Dashboard")
    parser.add_argument("--web", action="store_true", help="Generate web dashboard (HTML)")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds")
    args = parser.parse_args()
    
    dashboard = CompressionDashboard()
    dashboard.run(web=args.web, interval=args.interval)


if __name__ == "__main__":
    main()
