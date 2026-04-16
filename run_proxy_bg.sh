#!/bin/bash
cd /home/cheta/code/claude-code-proxy
source .venv/bin/activate
exec python start_proxy.py --skip-validation >> /tmp/proxy-logs/proxy.log 2>&1
