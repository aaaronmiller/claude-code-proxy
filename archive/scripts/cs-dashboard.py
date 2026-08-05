#!/usr/bin/env python3
"""
Compression Stack + Claude Code Proxy — CLI Dashboard
Displays live usage stats from both Headroom compression proxies AND
Claude Code Proxy (when present). Auto-detects what's running.

Usage:
    python3 cs-dashboard.py              # One-shot display
    python3 cs-dashboard.py --watch      # Live refresh every 2s
    python3 cs-dashboard.py --port 9999  # Custom web dashboard port
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

# ─── Colors & Icons ───────────────────────────────────────────────────────────
C_RESET   = '\033[0m'
C_BOLD    = '\033[1m'
C_DIM     = '\033[2m'
C_RED     = '\033[38;5;196m'
C_GREEN   = '\033[38;5;82m'
C_YELLOW  = '\033[38;5;226m'
C_CYAN    = '\033[38;5;87m'
C_MAGENTA = '\033[38;5;212m'
C_WHITE   = '\033[38;5;255m'
C_GRAY    = '\033[38;5;245m'
C_ORANGE  = '\033[38;5;208m'
C_BLUE    = '\033[38;5;75m'

def fmt(num):
    """Format number with commas."""
    if isinstance(num, (int, float)):
        return f"{num:,.0f}"
    return str(num)

def tok_fmt(n):
    """Format tokens with K/M suffix."""
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def ms_fmt(ms):
    """Format milliseconds."""
    ms = int(ms)
    if ms >= 1000:
        return f"{ms/1000:.1f}s"
    return f"{ms}ms"

def status_dot(ok):
    return f"{C_GREEN}●{C_RESET}" if ok else f"{C_RED}●{C_RESET}"

def pct(val, total, width=20):
    """Draw a mini progress bar."""
    if total == 0:
        filled = 0
    else:
        filled = int((val / total) * width)
    bar = f"{C_GREEN}{'█' * filled}{C_DIM}{'░' * (width - filled)}{C_RESET}"
    return bar

# ─── Data Sources ─────────────────────────────────────────────────────────────

def http_get(url, timeout=2):
    """Simple HTTP GET returning parsed JSON or None."""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def get_headroom_health(port):
    data = http_get(f"http://127.0.0.1:{port}/health")
    if data:
        return {
            "running": True,
            "version": data.get("version", "?"),
            "optimize": data.get("config", {}).get("optimize", False),
            "cache": data.get("config", {}).get("cache", False),
            "rate_limit": data.get("config", {}).get("rate_limit", False),
        }
    return {"running": False, "version": "?", "optimize": False, "cache": False, "rate_limit": False}

def parse_headroom_logs(log_file):
    """Parse Headroom JSONL log for stats."""
    stats = {
        "requests": 0, "compressed": 0,
        "tokens_in": 0, "tokens_out": 0, "tokens_saved": 0,
        "latencies": [],
    }
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    stats["requests"] += 1
                    ti = evt.get("tokens_in", evt.get("input_tokens", 0))
                    to = evt.get("tokens_out", evt.get("output_tokens", 0))
                    stats["tokens_in"] += ti
                    stats["tokens_out"] += to
                    if ti > 0:
                        saved = max(0, ti - to)
                        stats["tokens_saved"] += saved
                    lat = evt.get("latency_ms", evt.get("latency", 0))
                    if lat:
                        stats["latencies"].append(lat)
                    tags = json.dumps(evt).lower()
                    if any(k in tags for k in ["compress", "optimize", "cache_hit", "save"]):
                        stats["compressed"] += 1
                except:
                    continue
    except:
        pass
    return stats

def get_ccp_stats():
    """Get Claude Code Proxy usage stats."""
    data = http_get("http://127.0.0.1:8082/api/stats")
    if not data:
        return None
    return {
        "running": True,
        "requests_today": data.get("requests_today", 0),
        "total_tokens": data.get("total_tokens", 0),
        "est_cost": data.get("est_cost", 0),
        "avg_latency": data.get("avg_latency", 0),
        "recent_requests": data.get("recent_requests", []),
    }

def get_ccp_health():
    """Get CCP health status."""
    data = http_get("http://127.0.0.1:8082/health")
    if data:
        return {"running": True, "timestamp": data.get("timestamp", "?")}
    return {"running": False}

def get_rtk_version():
    try:
        r = subprocess.run(["rtk", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()
    except:
        pass
    return None

def get_gpu_info():
    """Detect GPU info for display."""
    # Try clinfo first (Intel)
    try:
        r = subprocess.run(["clinfo"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for line in r.stdout.split('\n'):
                if 'Device Name' in line and '0x569' in line:
                    name = line.split('Intel(R)')[-1].strip()
                    return f"Intel Arc {name}"
    except:
        pass
    # Try nvidia-smi
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                          capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return f"NVIDIA {r.stdout.strip().split(chr(10))[0]}"
    except:
        pass
    return None

def get_cli_sessions(limit=10):
    """Get recent CLI sessions."""
    sessions = []
    session_dirs = [
        (Path.home() / ".claude" / "sessions", "Claude Code", C_GREEN),
        (Path.home() / ".qwen" / "sessions", "Qwen Code", C_CYAN),
        (Path.home() / ".codex" / "sessions", "Codex CLI", C_ORANGE),
        (Path.home() / ".opencode" / "sessions", "OpenCode", C_MAGENTA),
        (Path.home() / ".hermes" / "sessions", "Hermes", C_YELLOW),
    ]
    for session_dir, tool_name, color in session_dirs:
        if not session_dir.exists():
            continue
        for session_file in sorted(session_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                stat = session_file.stat()
                with open(session_file) as f:
                    data = json.load(f)
                sessions.append({
                    "tool": tool_name, "color": color,
                    "session": session_file.stem,
                    "modified": int(stat.st_mtime),
                    "size": stat.st_size,
                    "messages": len(data.get("messages", [])),
                    "cwd": data.get("cwd", data.get("workspace", "N/A")),
                })
            except:
                continue
    sessions.sort(key=lambda x: x["modified"], reverse=True)
    return sessions[:limit]

# ─── Display ──────────────────────────────────────────────────────────────────

def draw_separator(char='─', color=C_DIM):
    cols = os.get_terminal_size().columns if os.isatty(1) else 80
    print(f"{color}{char * cols}{C_RESET}")

def draw_header():
    cols = os.get_terminal_size().columns if os.isatty(1) else 80
    title = f"{C_BOLD}{C_CYAN}⚡ Compression Stack Monitor{C_RESET}"
    ts = f"{C_DIM}{datetime.now().strftime('%H:%M:%S')}{C_RESET}"
    pad = cols - len(title.replace('\033[0m','').replace('\033[1m','').replace('\033[38;5;87m','')) - len(ts.replace('\033[2m','').replace('\033[0m',''))
    if pad < 0: pad = 0
    print(f"\n{title}{' ' * pad}{ts}")
    draw_separator('═', C_CYAN)

def draw_section(title, icon='◆'):
    print(f"\n{C_BOLD}{C_MAGENTA}{icon} {title}{C_RESET}")
    draw_separator('─', C_MAGENTA)

def draw_kv(label, value, color=C_WHITE, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{C_DIM}{label}:{C_RESET} {color}{value}{C_RESET}")

def draw_metric(label, value, sub="", indent=0):
    prefix = "  " * indent
    print(f"{prefix}{C_BOLD}{C_CYAN}{label}{C_RESET}  {C_WHITE}{value}{C_RESET}{C_DIM} {sub}{C_RESET}")

def draw_bar(label, val, total, width=30, indent=0):
    prefix = "  " * indent
    if total == 0:
        filled = 0
        p = 0
    else:
        filled = int((val / total) * width)
        p = (val / total) * 100
    bar = f"{C_GREEN}{'█' * filled}{C_DIM}{'░' * (width - filled)}{C_RESET}"
    print(f"{prefix}{C_DIM}{label}:{C_RESET} {bar} {C_CYAN}{p:.0f}%{C_RESET}")

def display_dashboard():
    now = datetime.now()

    # Gather data
    hr_default = get_headroom_health(8787)
    hr_small = get_headroom_health(8790)
    ccp_health = get_ccp_health()
    ccp_stats = get_ccp_stats() if ccp_health["running"] else None
    rtk_ver = get_rtk_version()
    gpu = get_gpu_info()

    # Headroom log files
    hr_default_log = Path.home() / ".local/share/headroom/proxy-default.jsonl"
    hr_small_log = Path.home() / ".local/share/headroom/proxy-small.jsonl"
    hr_default_stats = parse_headroom_logs(hr_default_log) if hr_default_log.exists() else None
    hr_small_stats = parse_headroom_logs(hr_small_log) if hr_small_log.exists() else None

    draw_header()

    # ── GPU Info ──
    if gpu:
        draw_section("GPU Hardware", "󰢮")
        draw_kv("Device", gpu, C_GREEN)
        selector = os.environ.get("ONEAPI_DEVICE_SELECTOR", os.environ.get("CUDA_VISIBLE_DEVICES", "N/A"))
        draw_kv("Device Selector", selector, C_CYAN)

    # ── Headroom Status ──
    draw_section("Headroom Compression", "󱁙")

    # Default tier
    s_dot = status_dot(hr_default["running"])
    ver = hr_default["version"] if hr_default["running"] else "offline"
    draw_metric(f"Default {C_DIM}(:8787){C_RESET}", f"{s_dot}  {ver}", f"compress={'ON' if hr_default['optimize'] else 'OFF'}  cache={'ON' if hr_default['cache'] else 'OFF'}")

    # Small tier
    s_dot = status_dot(hr_small["running"])
    ver = hr_small["version"] if hr_small["running"] else "offline"
    draw_metric(f"Small   {C_DIM}(:8790){C_RESET}", f"{s_dot}  {ver}", f"compress={'ON' if hr_small['optimize'] else 'OFF'}  cache={'ON' if hr_small['cache'] else 'OFF'}")

    # Default stats
    if hr_default_stats and hr_default_stats["requests"] > 0:
        print()
        draw_metric("Default Requests", fmt(hr_default_stats["requests"]), "total")
        draw_metric("Tokens In", tok_fmt(hr_default_stats["tokens_in"]), "")
        draw_metric("Tokens Out", tok_fmt(hr_default_stats["tokens_out"]), "")
        saved = hr_default_stats["tokens_saved"]
        comp_rate = (saved / hr_default_stats["tokens_in"] * 100) if hr_default_stats["tokens_in"] > 0 else 0
        draw_metric("Tokens Saved", tok_fmt(saved), f"({comp_rate:.0f}% reduction)")
        if hr_default_stats["latencies"]:
            avg_lat = sum(hr_default_stats["latencies"]) / len(hr_default_stats["latencies"])
            draw_metric("Avg Latency", ms_fmt(avg_lat), "")

    # Small stats
    if hr_small_stats and hr_small_stats["requests"] > 0:
        print()
        draw_metric("Small Requests", fmt(hr_small_stats["requests"]), "total")
        draw_metric("Tokens In", tok_fmt(hr_small_stats["tokens_in"]), "")
        draw_metric("Tokens Out", tok_fmt(hr_small_stats["tokens_out"]), "")
        saved = hr_small_stats["tokens_saved"]
        comp_rate = (saved / hr_small_stats["tokens_in"] * 100) if hr_small_stats["tokens_in"] > 0 else 0
        draw_metric("Tokens Saved", tok_fmt(saved), f"({comp_rate:.0f}% reduction)")

    if (not hr_default_stats or hr_default_stats["requests"] == 0) and \
       (not hr_small_stats or hr_small_stats["requests"] == 0):
        print(f"\n{C_DIM}  No requests processed yet — traffic will appear here after use{C_RESET}")

    # ── Claude Code Proxy ──
    if ccp_health["running"]:
        draw_section("Claude Code Proxy", "󱃗")
        draw_kv("Status", f"{status_dot(True)} Healthy {C_DIM}(:8082){C_RESET}", C_GREEN)
        if ccp_stats:
            print()
            draw_metric("Requests Today", fmt(ccp_stats["requests_today"]), "")
            draw_metric("Total Tokens", tok_fmt(ccp_stats["total_tokens"]), "")
            draw_metric("Est. Cost", f"${ccp_stats['est_cost']:.4f}", "")
            if ccp_stats["avg_latency"] > 0:
                draw_metric("Avg Latency", ms_fmt(ccp_stats["avg_latency"]), "")
            if ccp_stats["recent_requests"]:
                print()
                print(f"  {C_DIM}Recent:{C_RESET}")
                for req in ccp_stats["recent_requests"][-5:]:
                    model = req.get("model", "unknown")[:30]
                    lat = req.get("latency_ms", 0)
                    tok = req.get("total_tokens", 0)
                    print(f"  {C_DIM}→{C_RESET} {C_CYAN}{model}{C_RESET}  {C_GRAY}{ms_fmt(lat)}{C_RESET}  {C_GRAY}{tok_fmt(tok)} tok{C_RESET}")
        else:
            print(f"\n{C_DIM}  No usage data yet — make some requests{C_RESET}")
    else:
        draw_section("Claude Code Proxy", "󱃗")
        print(f"  {C_RED}●{C_RESET} {C_YELLOW}Not running{C_RESET}  {C_DIM}(headroom compression active){C_RESET}")

    # ── RTK ──
    draw_section("RTK (Command Compression)", "󰞇")
    if rtk_ver:
        draw_kv("Version", rtk_ver, C_GREEN)
    else:
        draw_kv("Status", "Not installed", C_YELLOW)

    # ── CLI Sessions ──
    sessions = get_cli_sessions(8)
    if sessions:
        draw_section("CLI Sessions", "󰋁")
        # Table header
        h_tool = f"{'Tool':<14}"
        h_age = f"{'Age':<8}"
        h_msgs = f"{'Msgs':>5}"
        h_size = f"{'Size':>7}"
        h_cwd = f"{'Workspace'}"
        print(f"  {C_DIM}{h_tool} {h_age} {h_msgs} {h_size}  {h_cwd}{C_RESET}")
        draw_separator('─', C_DIM)
        now_ts = now.timestamp()
        for s in sessions:
            diff = now_ts - s["modified"]
            if diff < 60:
                age = f"{int(diff)}s"
            elif diff < 3600:
                age = f"{int(diff/60)}m"
            elif diff < 86400:
                age = f"{int(diff/3600)}h"
            else:
                age = f"{int(diff/86400)}d"
            sz = f"{s['size']/1024:.0f}K" if s['size'] < 1048576 else f"{s['size']/1048576:.1f}M"
            tool = s["tool"][:13]
            cwd = s["cwd"].split('/')[-1] if '/' in s["cwd"] else s["cwd"]
            if len(cwd) > 25:
                cwd = "…" + cwd[-24:]
            color = s["color"]
            print(f"  {color}{tool:<14}{C_RESET} {C_GRAY}{age:<8}{C_RESET} {C_WHITE}{s['messages']:>5}{C_RESET} {C_GRAY}{sz:>7}{C_RESET}  {C_DIM}{cwd}{C_RESET}")

    # Footer
    print()
    draw_separator('═', C_CYAN)
    print(f"  {C_DIM}Auto-refresh: press Ctrl+C to stop | Data from Headroom (:8787/:8790) + CCP (:8082){C_RESET}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    watch = "--watch" in sys.argv
    if watch:
        try:
            while True:
                os.system('clear' if os.name != 'nt' else 'cls')
                display_dashboard()
                time.sleep(2)
        except KeyboardInterrupt:
            print(f"\n{C_DIM}Dashboard stopped{C_RESET}")
    else:
        display_dashboard()

if __name__ == "__main__":
    main()
