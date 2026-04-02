#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTROL="$ROOT_DIR/bin/compressctl"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/quickstart.sh [options]

Options:
  --check                  Show current detected status and exit
  --yes                    Skip interactive target selection
  --targets <list>         Comma-separated targets or "detected"
  --headroom-only          Install only Headroom-related pieces
  --rtk-only               Install only RTK-related pieces

Examples:
  ./scripts/quickstart.sh
  ./scripts/quickstart.sh --check
  ./scripts/quickstart.sh --yes --targets claude,qwen,codex
EOF
}

check_only=0
assume_yes=0
targets="detected"
extra_flags=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      check_only=1
      ;;
    --yes)
      assume_yes=1
      ;;
    --targets)
      shift
      targets="${1:-detected}"
      ;;
    --targets=*)
      targets="${1#*=}"
      ;;
    --headroom-only|--rtk-only)
      extra_flags+=("$1")
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "quickstart: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift || true
done

if [[ $check_only -eq 1 ]]; then
  exec "$CONTROL" check
fi

if [[ "$targets" == "detected" && $assume_yes -eq 0 && -t 0 && -t 1 ]]; then
  echo "Detected targets:"
  mapfile -t detected < <("$CONTROL" list)
  printf '  - %s\n' "${detected[@]}"
  echo
  printf "Install for detected targets? [Y/n]: "
  read -r answer
  case "${answer:-Y}" in
    n|N|no|NO)
      printf "Enter comma-separated targets: "
      read -r targets
      ;;
  esac
fi

exec "$CONTROL" install --targets "$targets" "${extra_flags[@]}"
