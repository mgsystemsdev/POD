#!/usr/bin/env bash
# Starts the Task Dashboard server from ~/agents/agent-services/
# Usage: bash ~/agents/agent-services/system/scripts/start_dashboard.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(cd "$SCRIPT_DIR/../dashboard" && pwd)"

echo "Starting Task Dashboard → http://localhost:8765"
echo "Tasks:  ~/.claude/tasks.json"
echo "Logs:   ~/agents/agent-services/logs/dashboard.log"

ENV_FILE="${HOME}/agents/agent-services/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

python3 "$DASHBOARD_DIR/server.py"
