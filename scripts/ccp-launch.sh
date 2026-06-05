#!/usr/bin/env bash
# ccp launcher: session-scoped routing profiles for CLI tools.

set -euo pipefail

PROXY_URL="${CCP_PROXY_URL:-http://127.0.0.1:8082}"
PROXY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_ID=""
PRESET="default"
POLICY=""
PROVIDER=""
ROLE=""
CONFIG_FILE=""
NO_COMPRESS=false
CONTINUE=false

emit_launcher_error() {
  local message="$1"
  python3 - "$message" "$cmd" "$PROFILE_ID" <<'PY' >/dev/null 2>&1 || true
import sys
from src.services.observability.error_sink import emit_error
message, tool, session_id = sys.argv[1:4]
emit_error(message, tool=tool, session_id=session_id, component="launcher")
PY
}

usage() {
  cat <<'EOF'
Usage:
  ccp up [--background]
  ccp errors [--follow] [--tool NAME] [--provider NAME] [--session ID]
  ccp <claude|codex|qwen|opencode|hermes|ante|antigravity> [options] [-- extra args]

Options:
  --preset NAME       base routing profile (default: tool name)
  --config PATH       JSON session overlay file
  --role ROLE         set requested role metadata on the session profile
  --policy POLICY     override model_scan policy for launched session metadata
  --provider NAME     profile provider_override
  --no-compress       do not wrap command in rtk
  --continue          pass resume/continue flag where supported
EOF
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

proxy_up() {
  if curl -sf --max-time 1 "$PROXY_URL/health" >/dev/null 2>&1; then
    return 0
  fi
  PROXIES_NO_ATTACH=1 "$PROXY_DIR/proxies" up >/dev/null 2>&1 || true
}

make_overlay() {
  python3 - "$CONFIG_FILE" "$POLICY" "$PROVIDER" "$ROLE" <<'PY'
import json, sys
path, policy, provider, role = sys.argv[1:5]
overlay = {}
if path:
    with open(path, "r", encoding="utf-8") as f:
        overlay.update(json.load(f))
if policy:
    overlay["policy"] = policy
if provider:
    overlay["provider_override"] = provider
if role:
    overlay["requested_role"] = role
print(json.dumps(overlay))
PY
}

create_profile() {
  local overlay_json="$1"
  local payload
  payload=$(python3 - "$PRESET" "$overlay_json" <<'PY'
import json, sys
preset, overlay = sys.argv[1], json.loads(sys.argv[2])
print(json.dumps({"preset": preset, "overlay": overlay, "ttl_s": 86400}))
PY
)
  curl -sf -H 'content-type: application/json' -d "$payload" "$PROXY_URL/api/routing-profiles"
}

delete_profile() {
  if [ -n "$PROFILE_ID" ]; then
    curl -sf -X DELETE "$PROXY_URL/api/routing-profiles/$PROFILE_ID" >/dev/null 2>&1 || true
  fi
}

run_errors() {
  shift || true
  python3 "$PROXY_DIR/scripts/ccp_errors.py" "$@"
}

run_up() {
  shift || true
  local background=false
  while [ $# -gt 0 ]; do
    case "$1" in
      --background) background=true ;;
      -h|--help) echo "Usage: ccp up [--background]"; return 0 ;;
      *) echo "unknown ccp up option: $1" >&2; return 2 ;;
    esac
    shift
  done
  if [ "$background" = true ]; then
    PROXIES_NO_ATTACH=1 "$PROXY_DIR/proxies" up
    return
  fi
  if command -v wezterm >/dev/null 2>&1 && [ -z "${CCP_NO_WEZTERM:-}" ]; then
    wezterm start --cwd "$PROXY_DIR" -- "$PROXY_DIR/proxies" up
  else
    "$PROXY_DIR/proxies" up
  fi
}

tool_command() {
  local tool="$1"
  local base="$PROXY_URL/p/$PROFILE_ID"
  case "$tool" in
    claude)
      export ANTHROPIC_BASE_URL="$base"
      export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-pass}"
      if [ "$CONTINUE" = true ]; then echo "claude --continue"; else echo "claude"; fi
      ;;
    codex)
      export OPENAI_BASE_URL="$base/v1"
      export OPENAI_API_KEY="${OPENAI_API_KEY:-pass}"
      if [ "$CONTINUE" = true ]; then echo "codex resume"; else echo "codex"; fi
      ;;
    qwen)
      export OPENAI_BASE_URL="$base/v1"
      export OPENAI_API_KEY="${OPENAI_API_KEY:-pass}"
      if [ "$CONTINUE" = true ]; then echo "qwen --auth-type openai --continue"; else echo "qwen --auth-type openai"; fi
      ;;
    opencode)
      export OPENAI_BASE_URL="$base/v1"
      export OPENAI_API_KEY="${OPENAI_API_KEY:-pass}"
      if [ "$CONTINUE" = true ]; then echo "opencode --resume"; else echo "opencode"; fi
      ;;
    hermes|ante|antigravity)
      export OPENAI_BASE_URL="$base/v1"
      export OPENAI_API_KEY="${OPENAI_API_KEY:-pass}"
      if [ "$CONTINUE" = true ]; then echo "$tool --continue"; else echo "$tool"; fi
      ;;
  *) echo ""; return 1 ;;
  esac
}

if [ $# -eq 0 ]; then usage; exit 0; fi

cmd="$1"
case "$cmd" in
  -h|--help) usage; exit 0 ;;
  up) run_up "$@"; exit $? ;;
  errors) run_errors "$@"; exit $? ;;
esac

tool="$cmd"; shift
PRESET="$tool"
extra=()
while [ $# -gt 0 ]; do
  case "$1" in
    --preset) PRESET="$2"; shift 2 ;;
    --config) CONFIG_FILE="$2"; shift 2 ;;
    --role) ROLE="$2"; shift 2 ;;
    --policy) POLICY="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --no-compress) NO_COMPRESS=true; shift ;;
    --continue) CONTINUE=true; shift ;;
    --) shift; extra+=("$@"); break ;;
    *) extra+=("$1"); shift ;;
  esac
done

proxy_up
overlay_json="$(make_overlay)"
profile_json="$(create_profile "$overlay_json")"
PROFILE_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"$profile_json")"
trap delete_profile EXIT

cmdline="$(tool_command "$tool")"
if [ -z "$cmdline" ]; then
  echo "unknown tool: $tool" >&2
  emit_launcher_error "unknown tool: $tool"
  exit 2
fi

if [ "$NO_COMPRESS" = false ] && command -v rtk >/dev/null 2>&1; then
  exec rtk $cmdline "${extra[@]}"
fi
exec $cmdline "${extra[@]}"
