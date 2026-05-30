#!/usr/bin/env bash
# Start a human_control baseline session.
#
# Usage: scripts/start_human_session.sh <run_id>
#
# 1. Ensures ~/sessions/<run_id>/code/ exists with a manifest.json
# 2. Opens the code folder in VS Code
# 3. Starts the keystroke recorder in the foreground (Ctrl+C to stop)
set -euo pipefail

RUN_ID="${1:-run_001}"
SESSION_DIR="${HOME}/sessions/${RUN_ID}"
CODE_DIR="${SESSION_DIR}/code"
LOG_PATH="${SESSION_DIR}/log.json"

mkdir -p "${CODE_DIR}"
[[ -f "${CODE_DIR}/manifest.json" ]] || echo "[]" > "${CODE_DIR}/manifest.json"

echo "[session] run_id    = ${RUN_ID}"
echo "[session] code dir  = ${CODE_DIR}"
echo "[session] log file  = ${LOG_PATH}"
echo

if command -v code >/dev/null 2>&1; then
  code "${CODE_DIR}"
  echo "[session] opened VS Code on ${CODE_DIR}"
else
  echo "[session] 'code' CLI not on PATH — open ${CODE_DIR} in VS Code manually"
fi

echo
echo "[session] starting keystroke recorder. DO NOT TYPE YET in VS Code"
echo "[session] until you see the 'capturing keystrokes' line below."
echo "[session] Press Ctrl+C here when your coding session is finished."
echo

cd "$(dirname "$0")/.."
exec python -m auditor.adapters.human_control_recorder --record --out "${LOG_PATH}"
