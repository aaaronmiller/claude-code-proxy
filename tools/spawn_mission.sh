#!/bin/bash
# tools/spawn_mission.sh — The God Tool
# Usage: ./tools/spawn_mission.sh <mission_objective> [mission_id]
# Creates a mission directory, injects .claude config, and spawns a headless Claude instance

set -euo pipefail

MISSION_OBJECTIVE="${1:?Usage: spawn_mission.sh <objective> [mission_id]}"
MISSION_ID="${2:-mission_$(date +%s)}"

# Paths
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
MISSION_DIR="/tmp/missions/${MISSION_ID}"
AGENT_ARSENAL="${HOME}/agent-arsenal"

# 1. Isolate: Create mission directory
mkdir -p "${MISSION_DIR}"
echo "[spawn] Created mission directory: ${MISSION_DIR}"

# 2. Inject: Copy .claude config from arsenal (or current project)
if [ -d "${AGENT_ARSENAL}/.claude" ]; then
  cp -r "${AGENT_ARSENAL}/.claude" "${MISSION_DIR}/"
  echo "[spawn] Injected .claude from arsenal"
elif [ -d "${PROJECT_DIR}/.claude" ]; then
  cp -r "${PROJECT_DIR}/.claude" "${MISSION_DIR}/"
  echo "[spawn] Injected .claude from project"
else
  echo "[spawn] WARNING: No .claude directory found — using bare config"
  mkdir -p "${MISSION_DIR}/.claude"
fi

# 3. Write mission objective
cat > "${MISSION_DIR}/MISSION.md" << EOF
# Mission: ${MISSION_ID}
**Objective:** ${MISSION_OBJECTIVE}
**Started:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Status:** active
EOF

# 4. Update state
if [ -f "${PROJECT_DIR}/.claude/state/current_mission.json" ]; then
  python3 -c "
import json, sys
with open('${PROJECT_DIR}/.claude/state/current_mission.json') as f:
    state = json.load(f)
state['mission_id'] = '${MISSION_ID}'
state['objective'] = '''${MISSION_OBJECTIVE}'''
state['phase'] = 'scouting'
state['status'] = 'in_progress'
state['last_updated'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
with open('${PROJECT_DIR}/.claude/state/current_mission.json', 'w') as f:
    json.dump(state, f, indent=2)
"
fi

# 5. Ignite: Spawn headless Claude
echo "[spawn] Launching Claude headless in ${MISSION_DIR}..."
cd "${MISSION_DIR}" && claude -p "${MISSION_OBJECTIVE}" --headless --output-format stream-json 2>&1 | tee "${MISSION_DIR}/output.log"

# 6. Return PID for MACS tracking
CLAUDE_PID=$!
echo "[spawn] Claude PID: ${CLAUDE_PID}"
echo "${CLAUDE_PID}" > "${MISSION_DIR}/.pid"

# 7. Report back
echo "[spawn] Mission ${MISSION_ID} complete. Results in ${MISSION_DIR}/"
