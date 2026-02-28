#!/bin/bash
cd /home/cheta/code/claude-code-proxy
source .venv/bin/activate
# Kill any existing on 8082 just in case
fuser -k 8082/tcp 2>/dev/null
# Start with unbuffered output
python -u start_proxy.py --skip-validation > proxy_debug.log 2>&1 &
echo $! > proxy.pid
sleep 2
cat proxy_debug.log
