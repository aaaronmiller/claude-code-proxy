#!/bin/bash
cd /home/cheta/code/claude-code-proxy
source .venv/bin/activate
source .env 2>/dev/null
echo "BIG_MODEL=$BIG_MODEL"
echo "MIDDLE_MODEL=$MIDDLE_MODEL"  
echo "SMALL_MODEL=$SMALL_MODEL"
LOG_LEVEL=info python start_proxy.py --skip-validation
