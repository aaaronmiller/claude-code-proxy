#!/usr/bin/env python3
"""
Input Compression Stack Web Dashboard
Serves a web UI for monitoring Headroom + RTK compression layers
Part of the input-compression project
Usage: python scripts/compress-monitor-web.py [--port 8899]
"""

import http.server
import socketserver
import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899

# Load input-compression state
STATE_FILE = Path.home() / ".config" / "input-compression" / "state.env"
HEADROOM_PORT = 8787
HEADROOM_SMALL_PORT = 8790

if STATE_FILE.exists():
    with open(STATE_FILE) as f:
        for line in f:
            if line.startswith("HEADROOM_PORT="):
                HEADROOM_PORT = int(line.strip().split("=")[1])
            elif line.startswith("HEADROOM_SMALL_PORT="):
                HEADROOM_SMALL_PORT = int(line.strip().split("=")[1])


def get_headroom_health(port):
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return {
                "running": True,
                "optimize": data.get("config", {}).get("optimize", False),
                "cache": data.get("config", {}).get("cache", False)
            }
    except:
        return {"running": False, "optimize": False, "cache": False}


def get_headroom_stats(log_file):
    stats = {"requests": 0, "compressed": 0, "tokens_in": 0, "tokens_out": 0}
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    stats["requests"] += 1
                    if any(k in str(event).lower() for k in ["compress", "optimize", "save"]):
                        stats["compressed"] += 1
                    stats["tokens_in"] += event.get("tokens_in", event.get("input_tokens", 0))
                    stats["tokens_out"] += event.get("tokens_out", event.get("output_tokens", 0))
                except:
                    continue
    except:
        pass
    return stats


def get_rtk_status():
    try:
        result = subprocess.run(["rtk", "--version"], capture_output=True, text=True, timeout=5)
        return {"installed": True, "version": result.stdout.strip() if result.returncode == 0 else "unknown"}
    except:
        return {"installed": False, "version": None}


def get_rtk_stats():
    stats = {"total_compressions": 0, "tokens_saved": 0, "last_compression": None}
    try:
        result = subprocess.run(["rtk", "gain", "--history"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            stats["total_compressions"] = len([l for l in lines if l.strip()])
            if lines and lines[0].strip():
                stats["last_compression"] = lines[0].strip()[:100]
    except:
        pass
    return stats


def get_cli_sessions():
    sessions = []
    session_dirs = [
        (Path.home() / ".claude" / "sessions", "Claude Code"),
        (Path.home() / ".qwen" / "sessions", "Qwen Code"),
        (Path.home() / ".codex" / "sessions", "Codex CLI"),
        (Path.home() / ".opencode" / "sessions", "OpenCode"),
    ]

    for session_dir, tool_name in session_dirs:
        if not session_dir.exists():
            continue
        for session_file in session_dir.glob("*.json"):
            try:
                stat = session_file.stat()
                with open(session_file) as f:
                    data = json.load(f)
                sessions.append({
                    "tool": tool_name,
                    "session": session_file.stem,
                    "modified": int(stat.st_mtime),
                    "size": stat.st_size,
                    "messages": len(data.get("messages", [])),
                    "cwd": data.get("cwd", data.get("workspace", "N/A")),
                })
            except:
                continue

    sessions.sort(key=lambda x: x["modified"], reverse=True)
    return sessions[:20]


def get_dashboard_data():
    return {
        "timestamp": datetime.now().isoformat(),
        "headroom": {
            "default": get_headroom_health(HEADROOM_PORT),
            "small": get_headroom_health(HEADROOM_SMALL_PORT),
            "default_stats": get_headroom_stats(Path.home() / ".local/share/headroom/proxy-default.jsonl"),
            "small_stats": get_headroom_stats(Path.home() / ".local/share/headroom/proxy-small.jsonl")
        },
        "rtk": get_rtk_status(),
        "rtk_stats": get_rtk_stats(),
        "sessions": get_cli_sessions()
    }


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Input Compression - Status Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f1a; color: #e0e0e0; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #00d4ff; margin-bottom: 10px; font-size: 28px; }
        h2 { color: #7b68ee; margin: 20px 0 10px; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 5px; }
        .subtitle { color: #888; margin-bottom: 20px; font-size: 14px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: #1a1a2e; border-radius: 8px; padding: 20px; border: 1px solid #333; }
        .card h3 { color: #00d4ff; margin-bottom: 15px; font-size: 16px; }
        .status-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2a3e; }
        .status-row:last-child { border-bottom: none; }
        .label { color: #aaa; }
        .value { font-weight: bold; }
        .value.good { color: #00ff88; }
        .value.bad { color: #ff4757; }
        .value.warn { color: #ffa502; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #2a2a3e; }
        th { color: #7b68ee; font-weight: 600; font-size: 13px; }
        td { font-size: 13px; }
        .tool-claude { color: #00ff88; }
        .tool-qwen { color: #00d4ff; }
        .tool-codex { color: #ffa502; }
        .tool-opencode { color: #ff6b9d; }
        .refresh-btn { background: #7b68ee; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; margin-bottom: 20px; }
        .refresh-btn:hover { background: #6a5acd; }
        .auto-refresh { color: #666; font-size: 12px; margin-left: 10px; }
        .metric-big { font-size: 24px; font-weight: bold; color: #00d4ff; }
        .metric-label { color: #888; font-size: 12px; margin-top: 5px; }
        .section-link { color: #7b68ee; text-decoration: none; margin-left: 10px; font-size: 13px; }
        .section-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Input Compression Monitor</h1>
        <p class="subtitle">Headroom + RTK Real-time Status | <a href="https://github.com/chopratejas/headroom" class="section-link" target="_blank">Headroom Docs</a> | <a href="https://github.com/input-compression/rtk" class="section-link" target="_blank">RTK Docs</a></p>
        <button class="refresh-btn" onclick="loadData()">↻ Refresh</button>
        <span class="auto-refresh">Auto-refresh: 5s</span>
        <div id="dashboard"></div>
    </div>
    
    <script>
        function formatTime(ts) {
            const diff = Math.floor((Date.now() / 1000) - ts);
            if (diff < 60) return diff + 's ago';
            if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
            if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
            return Math.floor(diff / 86400) + 'd ago';
        }
        
        function formatNumber(n) { return n.toLocaleString(); }
        function formatSize(bytes) {
            if (bytes > 1048576) return (bytes / 1048576).toFixed(1) + 'MB';
            if (bytes > 1024) return (bytes / 1024).toFixed(1) + 'KB';
            return bytes + 'B';
        }
        
        function renderCard(title, content) {
            return `<div class="card"><h3>${title}</h3>${content}</div>`;
        }
        
        function renderStatusRow(label, value, className = '') {
            return `<div class="status-row"><span class="label">${label}</span><span class="value ${className}">${value}</span></div>`;
        }
        
        function loadData() {
            fetch('/api/data')
                .then(r => r.json())
                .then(data => {
                    let html = '';
                    
                    // Headroom Status
                    const hr = data.headroom;
                    html += '<h2>Headroom Compression</h2><div class="grid">';
                    
                    html += renderCard('Default Tier', 
                        renderStatusRow('Status', hr.default.running ? '✓ Running' : '✗ Offline', hr.default.running ? 'good' : 'bad') +
                        renderStatusRow('Compression', hr.default.optimize ? 'ON' : 'OFF', hr.default.optimize ? 'good' : 'warn') +
                        renderStatusRow('Cache', hr.default.cache ? 'ON' : 'OFF', hr.default.cache ? 'good' : 'warn')
                    );
                    
                    html += renderCard('Small Tier',
                        renderStatusRow('Status', hr.small.running ? '✓ Running' : '✗ Offline', hr.small.running ? 'good' : 'bad') +
                        renderStatusRow('Compression', hr.small.optimize ? 'ON' : 'OFF', hr.small.optimize ? 'good' : 'warn') +
                        renderStatusRow('Cache', hr.small.cache ? 'ON' : 'OFF', hr.small.cache ? 'good' : 'warn')
                    );
                    
                    html += renderCard('Default Stats',
                        `<div class="metric-big">${formatNumber(hr.default_stats.requests)}</div><div class="metric-label">Total Requests</div>` +
                        `<div style="margin-top:15px" class="metric-big">${formatNumber(hr.default_stats.tokens_in)}</div><div class="metric-label">Tokens In</div>` +
                        `<div style="margin-top:15px" class="metric-big">${formatNumber(hr.default_stats.tokens_out)}</div><div class="metric-label">Tokens Out</div>`
                    );
                    
                    html += renderCard('Small Stats',
                        `<div class="metric-big">${formatNumber(hr.small_stats.requests)}</div><div class="metric-label">Total Requests</div>` +
                        `<div style="margin-top:15px" class="metric-big">${formatNumber(hr.small_stats.tokens_in)}</div><div class="metric-label">Tokens In</div>` +
                        `<div style="margin-top:15px" class="metric-big">${formatNumber(hr.small_stats.tokens_out)}</div><div class="metric-label">Tokens Out</div>`
                    );
                    
                    html += '</div>';
                    
                    // RTK Status
                    html += '<h2>RTK (Real-Time Kompression)</h2><div class="grid">';
                    
                    html += renderCard('RTK Status',
                        renderStatusRow('Installed', data.rtk.installed ? '✓ Yes' : '✗ No', data.rtk.installed ? 'good' : 'bad') +
                        renderStatusRow('Version', data.rtk.version || 'N/A')
                    );
                    
                    html += renderCard('RTK Stats',
                        `<div class="metric-big">${formatNumber(data.rtk_stats.total_compressions)}</div><div class="metric-label">Total Compressions</div>` +
                        `<div style="margin-top:15px" class="metric-big">${formatNumber(data.rtk_stats.tokens_saved)}</div><div class="metric-label">Tokens Saved</div>`
                    );
                    
                    html += '</div>';
                    
                    // CLI Sessions
                    html += '<h2>CLI Sessions (Recent)</h2>';
                    if (data.sessions.length > 0) {
                        html += '<table><thead><tr><th>Tool</th><th>Session</th><th>Msg</th><th>Size</th><th>Age</th><th>Workspace</th></tr></thead><tbody>';
                        data.sessions.forEach(s => {
                            const toolClass = 'tool-' + s.tool.toLowerCase().replace(' ', '-');
                            html += `<tr>
                                <td class="${toolClass}">${s.tool}</td>
                                <td>${s.session.substring(0, 12)}${s.session.length > 12 ? '...' : ''}</td>
                                <td>${s.messages}</td>
                                <td>${formatSize(s.size)}</td>
                                <td>${formatTime(s.modified)}</td>
                                <td>${s.cwd.substring(Math.max(0, s.cwd.length - 30))}</td>
                            </tr>`;
                        });
                        html += '</tbody></table>';
                    } else {
                        html += '<p style="color:#666;padding:20px;text-align:center">No sessions found</p>';
                    }
                    
                    document.getElementById('dashboard').innerHTML = html;
                    document.querySelector('.subtitle').childNodes[0].textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleTimeString() + ' | ';
                })
                .catch(err => {
                    document.getElementById('dashboard').innerHTML = '<p style="color:#ff4757">Error loading data: ' + err + '</p>';
                });
        }
        
        loadData();
        setInterval(loadData, 5000);
    </script>
</body>
</html>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_dashboard_data()).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logging


if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Input Compression Dashboard running at http://localhost:{PORT}")
        print(f"API endpoint: http://localhost:{PORT}/api/data")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard stopped")
