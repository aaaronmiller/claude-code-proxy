#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
source .venv/bin/activate
echo "=== Python version ==="
python --version
echo "=== Testing imports ==="
python -c "
try:
    from src.core.config import Config
    print('Config import OK')
except Exception as e:
    print(f'Config import FAILED: {e}')

try:
    from src.main import app
    print('App import OK')
except Exception as e:
    print(f'App import FAILED: {e}')
"
echo "=== Starting proxy with 15s timeout ==="
set +e
timeout 15 python start_proxy.py --skip-validation 2>&1
exit_code=$?
set -e
echo "=== Exit code: $exit_code ==="
