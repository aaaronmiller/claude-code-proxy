#!/bin/bash
echo "=== Finding headroom ==="
find /home/cheta -name "headroom" -type f 2>/dev/null
find /usr/local -name "headroom" -type f 2>/dev/null
echo "=== Checking pip ==="
pip show headroom 2>/dev/null || echo "not in global pip"
/home/cheta/code/claude-code-proxy/.venv/bin/pip show headroom 2>/dev/null || echo "not in proxy venv pip"
echo "=== Checking cargo ==="
ls ~/.cargo/bin/headroom 2>/dev/null || echo "not in cargo"
echo "=== Checking systemd service ==="
cat ~/.config/systemd/user/headroom-proxy.service 2>/dev/null || echo "no systemd service"
echo "=== Checking snap ==="
snap list 2>/dev/null | grep -i headroom || echo "not in snap"
echo "=== Checking npm ==="
npm list -g headroom 2>/dev/null || echo "not in npm"
echo "=== docker check ==="
docker ps -a 2>/dev/null || echo "docker not available"
echo "=== PATH ==="
echo "$PATH"
