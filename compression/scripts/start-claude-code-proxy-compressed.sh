#!/usr/bin/env bash

set -euo pipefail

STATE_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/input-compression/state.env"
PROXY_DIR="${CLAUDE_CODE_PROXY_DIR:-$HOME/code/claude-code-proxy}"
DEBUG_TRAFFIC_LOG="${DEBUG_TRAFFIC_LOG:-false}"
RUNTIME_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/input-compression"
LOG_DIR="${HOME}/.local/share/headroom"

if [[ -f "$STATE_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$STATE_FILE"
fi

HEADROOM_PORT="${HEADROOM_PORT:-8787}"
HEADROOM_BIG_PORT="${HEADROOM_BIG_PORT:-8788}"
HEADROOM_MIDDLE_PORT="${HEADROOM_MIDDLE_PORT:-8789}"
HEADROOM_SMALL_PORT="${HEADROOM_SMALL_PORT:-8790}"
HEADROOM_MODE="${HEADROOM_MODE:-token_headroom}"
HEADROOM_DEFAULT_NO_OPTIMIZE="${HEADROOM_DEFAULT_NO_OPTIMIZE:-true}"
HEADROOM_BIG_NO_OPTIMIZE="${HEADROOM_BIG_NO_OPTIMIZE:-true}"
HEADROOM_MIDDLE_NO_OPTIMIZE="${HEADROOM_MIDDLE_NO_OPTIMIZE:-false}"
HEADROOM_SMALL_NO_OPTIMIZE="${HEADROOM_SMALL_NO_OPTIMIZE:-false}"
CLAUDE_PROXY_URL="${CLAUDE_PROXY_URL:-http://127.0.0.1:8082}"
OPENAI_UPSTREAM_URL="${OPENAI_UPSTREAM_URL:-https://openrouter.ai/api/v1}"

if [[ ! -d "$PROXY_DIR" ]]; then
  echo "claude-code-proxy dir not found: $PROXY_DIR" >&2
  exit 1
fi

cd "$PROXY_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

if [[ -f ".envrc" ]]; then
  # shellcheck disable=SC1091
  source ".envrc"
fi

mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

bool_enabled() {
  case "${1:-false}" in
    true|TRUE|1|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

detect_provider() {
  local url="${1:-}"
  local lower="${url,,}"
  if [[ "$lower" == *"openrouter.ai"* ]]; then
    echo "openrouter"
  elif [[ "$lower" == *"127.0.0.1:8317"* || "$lower" == *"localhost:8317"* || "$lower" == *"gemini"* || "$lower" == *"googleapis.com"* ]]; then
    echo "gemini"
  elif [[ "$lower" == *"api.openai.com"* ]]; then
    echo "openai"
  elif [[ "$lower" == *"anthropic.com"* ]]; then
    echo "anthropic"
  elif [[ "$lower" == *"azure"* || "$lower" == *".openai.azure.com"* ]]; then
    echo "azure"
  elif [[ "$lower" == *"kiro"* || "$lower" == *"127.0.0.1:8083"* || "$lower" == *"localhost:8083"* ]]; then
    echo "kiro"
  else
    echo "openai_compatible"
  fi
}

start_headroom_instance() {
  local name="$1"
  local port="$2"
  local upstream="$3"
  local no_optimize="${4:-false}"
  local pid_file="$RUNTIME_DIR/headroom-${name}.pid"
  local log_file="$LOG_DIR/proxy-${name}.jsonl"
  local listener_pid=""

  if command -v lsof >/dev/null 2>&1; then
    listener_pid="$(lsof -tiTCP:${port} -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  fi

  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$existing_pid" && -d "/proc/$existing_pid" ]]; then
      local cmdline
      cmdline="$(tr '\0' ' ' < "/proc/$existing_pid/cmdline" 2>/dev/null || true)"
      if [[ "$cmdline" == *"headroom proxy"* && "$cmdline" == *"--port ${port}"* && "$cmdline" == *"--openai-api-url ${upstream}"* ]]; then
        if [[ "$no_optimize" == "true" && "$cmdline" != *"--no-optimize"* ]]; then
          :
        elif [[ "$no_optimize" != "true" && "$cmdline" == *"--no-optimize"* ]]; then
          :
        else
          return 0
        fi
      fi
      if [[ "$cmdline" == *"headroom proxy"* && "$cmdline" == *"--port ${port}"* ]]; then
        kill "$existing_pid" 2>/dev/null || true
        sleep 1
      fi
    fi
    rm -f "$pid_file"
  fi

  if [[ -n "$listener_pid" && -d "/proc/$listener_pid" ]]; then
    local listener_cmdline
    listener_cmdline="$(tr '\0' ' ' < "/proc/$listener_pid/cmdline" 2>/dev/null || true)"
    if [[ "$listener_cmdline" == *"headroom proxy"* && "$listener_cmdline" == *"--port ${port}"* && "$listener_cmdline" == *"--openai-api-url ${upstream}"* ]]; then
      if [[ "$no_optimize" == "true" && "$listener_cmdline" != *"--no-optimize"* ]]; then
        :
      elif [[ "$no_optimize" != "true" && "$listener_cmdline" == *"--no-optimize"* ]]; then
        :
      else
        echo "$listener_pid" > "$pid_file"
        return 0
      fi
    fi
    if [[ "$listener_cmdline" == *"headroom proxy"* && "$listener_cmdline" == *"--port ${port}"* ]]; then
      kill "$listener_pid" 2>/dev/null || true
      sleep 1
    else
      echo "Port ${port} is already in use by a non-headroom process; cannot start tier '${name}'" >&2
      exit 1
    fi
  fi

  local cmd=(
    headroom proxy
    --port "$port"
    --mode "$HEADROOM_MODE"
    --openai-api-url "$upstream"
    --log-file "$log_file"
    --no-telemetry
  )
  if [[ "$no_optimize" == "true" ]]; then
    cmd+=(--no-optimize)
  fi

  nohup "${cmd[@]}" >/dev/null 2>&1 &
  echo "$!" > "$pid_file"
}

DEFAULT_UPSTREAM_URL="${PROVIDER_BASE_URL:-${OPENAI_BASE_URL:-$OPENAI_UPSTREAM_URL}}"
BIG_UPSTREAM_URL="$DEFAULT_UPSTREAM_URL"
MIDDLE_UPSTREAM_URL="$DEFAULT_UPSTREAM_URL"
SMALL_UPSTREAM_URL="$DEFAULT_UPSTREAM_URL"

if bool_enabled "${ENABLE_BIG_ENDPOINT:-false}" && [[ -n "${BIG_ENDPOINT:-}" ]]; then
  BIG_UPSTREAM_URL="$BIG_ENDPOINT"
fi
if bool_enabled "${ENABLE_MIDDLE_ENDPOINT:-false}" && [[ -n "${MIDDLE_ENDPOINT:-}" ]]; then
  MIDDLE_UPSTREAM_URL="$MIDDLE_ENDPOINT"
fi
if bool_enabled "${ENABLE_SMALL_ENDPOINT:-false}" && [[ -n "${SMALL_ENDPOINT:-}" ]]; then
  SMALL_UPSTREAM_URL="$SMALL_ENDPOINT"
fi

DEFAULT_PROVIDER="$(detect_provider "$DEFAULT_UPSTREAM_URL")"
BIG_PROVIDER="$(detect_provider "$BIG_UPSTREAM_URL")"
MIDDLE_PROVIDER="$(detect_provider "$MIDDLE_UPSTREAM_URL")"
SMALL_PROVIDER="$(detect_provider "$SMALL_UPSTREAM_URL")"

start_headroom_instance "default" "$HEADROOM_PORT" "$DEFAULT_UPSTREAM_URL" "$HEADROOM_DEFAULT_NO_OPTIMIZE"

export PROVIDER_BASE_URL="http://127.0.0.1:${HEADROOM_PORT}/v1"
export OPENAI_BASE_URL="$PROVIDER_BASE_URL"
export DEFAULT_PROVIDER="$DEFAULT_PROVIDER"

export HEADROOM_DEFAULT_UPSTREAM_URL="$DEFAULT_UPSTREAM_URL"
export CLAUDE_PROXY_URL

BIG_STATUS="disabled"
MIDDLE_STATUS="disabled"
SMALL_STATUS="disabled"

if bool_enabled "${ENABLE_BIG_ENDPOINT:-false}"; then
  start_headroom_instance "big" "$HEADROOM_BIG_PORT" "$BIG_UPSTREAM_URL" "$HEADROOM_BIG_NO_OPTIMIZE"
  export BIG_ENDPOINT="http://127.0.0.1:${HEADROOM_BIG_PORT}/v1"
  export BIG_PROVIDER="$BIG_PROVIDER"
  export HEADROOM_BIG_UPSTREAM_URL="$BIG_UPSTREAM_URL"
  BIG_STATUS="enabled"
fi

if bool_enabled "${ENABLE_MIDDLE_ENDPOINT:-false}"; then
  start_headroom_instance "middle" "$HEADROOM_MIDDLE_PORT" "$MIDDLE_UPSTREAM_URL" "$HEADROOM_MIDDLE_NO_OPTIMIZE"
  export MIDDLE_ENDPOINT="http://127.0.0.1:${HEADROOM_MIDDLE_PORT}/v1"
  export MIDDLE_PROVIDER="$MIDDLE_PROVIDER"
  export HEADROOM_MIDDLE_UPSTREAM_URL="$MIDDLE_UPSTREAM_URL"
  MIDDLE_STATUS="enabled"
fi

if bool_enabled "${ENABLE_SMALL_ENDPOINT:-false}"; then
  start_headroom_instance "small" "$HEADROOM_SMALL_PORT" "$SMALL_UPSTREAM_URL" "$HEADROOM_SMALL_NO_OPTIMIZE"
  export SMALL_ENDPOINT="http://127.0.0.1:${HEADROOM_SMALL_PORT}/v1"
  export SMALL_PROVIDER="$SMALL_PROVIDER"
  export HEADROOM_SMALL_UPSTREAM_URL="$SMALL_UPSTREAM_URL"
  SMALL_STATUS="enabled"
fi

echo "Starting Claude Code proxy with compressed upstream in WSL/bash"
echo "  Claude -> ${CLAUDE_PROXY_URL}"
echo "  Proxy default -> ${PROVIDER_BASE_URL} -> ${DEFAULT_UPSTREAM_URL} (no-optimize=${HEADROOM_DEFAULT_NO_OPTIMIZE})"
echo "  Proxy big     -> ${BIG_STATUS}"
if [[ "$BIG_STATUS" == "enabled" ]]; then
  echo "                    ${BIG_ENDPOINT} -> ${BIG_UPSTREAM_URL} (no-optimize=${HEADROOM_BIG_NO_OPTIMIZE})"
fi
echo "  Proxy middle  -> ${MIDDLE_STATUS}"
if [[ "$MIDDLE_STATUS" == "enabled" ]]; then
  echo "                    ${MIDDLE_ENDPOINT} -> ${MIDDLE_UPSTREAM_URL} (no-optimize=${HEADROOM_MIDDLE_NO_OPTIMIZE})"
fi
echo "  Proxy small   -> ${SMALL_STATUS}"
if [[ "$SMALL_STATUS" == "enabled" ]]; then
  echo "                    ${SMALL_ENDPOINT} -> ${SMALL_UPSTREAM_URL} (no-optimize=${HEADROOM_SMALL_NO_OPTIMIZE})"
fi

if [[ "$DEBUG_TRAFFIC_LOG" == "true" ]]; then
  exec python start_proxy.py --skip-validation
else
  exec python start_proxy.py --skip-validation
fi
