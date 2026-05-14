#!/usr/bin/env bash
# ── Proxy Chain Watchdog ──────────────────────────────────────────────────────
# Runs inside a tmux pane. Checks each chain service's health every INTERVAL
# seconds. On failure: waits GRACE seconds, re-checks, then restarts the service
# via `proxies restart <id>` if still down.
#
# Env vars:
#   WATCHDOG_INTERVAL   — check frequency in seconds (default: 30)
#   WATCHDOG_GRACE      — seconds to wait before restarting after first failure (default: 5)
#   CHAIN_FILE          — path to proxy_chain.json
#   PROXY_DIR           — proxy root directory
# ─────────────────────────────────────────────────────────────────────────────

INTERVAL="${WATCHDOG_INTERVAL:-30}"
GRACE="${WATCHDOG_GRACE:-5}"
CHAIN_FILE="${CHAIN_FILE:-$PROXY_DIR/config/proxy_chain.json}"
PROXIES_CMD="${PROXY_DIR}/proxies"

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

log() { echo -e "$(date '+%H:%M:%S') [watchdog] $*"; }
ok()   { log "${GREEN}✓${NC} $*"; }
warn() { log "${YELLOW}⚠${NC} $*"; }
fail() { log "${RED}✗${NC} $*"; }

log "${CYAN}started${NC} — checking every ${INTERVAL}s  (grace: ${GRACE}s)"

health_check() {
    local port="$1" path="${2:-/health}"
    curl -sf --max-time 2 "http://127.0.0.1:${port}${path}" > /dev/null 2>&1
}

_chain_services() {
    python3 - <<PYEOF
import json, sys, os
path = os.environ.get("CHAIN_FILE", "$CHAIN_FILE")
try:
    data = json.loads(open(path).read())
except Exception:
    sys.exit(0)
entries = data.get("entries", [])
enabled = [e for e in entries if e.get("enabled") and e.get("service_cmd","")]
enabled.sort(key=lambda e: e.get("order", 0))
for e in enabled:
    print(f"{e['id']}|{e.get('name','?')}|{e.get('port',0)}|{e.get('health_path','/health')}")
PYEOF
}

declare -A failure_since

while true; do
    sleep "$INTERVAL"

    while IFS='|' read -r id name port health_path; do
        [ "${port:-0}" -gt 0 ] || continue

        if ! health_check "$port" "$health_path"; then
            if [ -z "${failure_since[$id]:-}" ]; then
                warn "$name :$port — unhealthy, waiting ${GRACE}s before restart"
                failure_since[$id]=$(date +%s)
                sleep "$GRACE"
            fi

            # Re-check after grace period
            if ! health_check "$port" "$health_path"; then
                fail "$name :$port — still down, restarting..."
                "${PROXIES_CMD}" restart "$id" 2>&1 | while IFS= read -r line; do
                    log "  $line"
                done
                unset "failure_since[$id]"
            else
                ok "$name :$port — recovered on its own"
                unset "failure_since[$id]"
            fi
        else
            # Clear failure state on success
            if [ -n "${failure_since[$id]:-}" ]; then
                ok "$name :$port — back healthy"
                unset "failure_since[$id]"
            fi
        fi
    done < <(CHAIN_FILE="$CHAIN_FILE" _chain_services)
done
