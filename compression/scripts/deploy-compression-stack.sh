#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

map_args=()
for arg in "$@"; do
  case "$arg" in
    --headroom) map_args+=("--headroom-only") ;;
    --rtk) map_args+=("--rtk-only") ;;
    *) map_args+=("$arg") ;;
  esac
done

exec "$ROOT_DIR/scripts/quickstart.sh" "${map_args[@]}"
